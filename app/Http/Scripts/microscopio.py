import cv2
import numpy as np
import datetime
import pymysql
import os
import sys
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
import traceback

# -------------------- Configuração --------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print("Aviso: falha ao configurar Gemini:", e, file=sys.stderr)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_DATABASE")

# -------------------- Funções --------------------
def conectar_banco():
    try:
        conexao = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Conectado com sucesso ao banco")
        return conexao
    except pymysql.MySQLError as err:
        print(f"Erro ao conectar ao banco: {err}", file=sys.stderr)
        raise

def buscar_paciente_por_cpf(conexao, cpf_str):
    cpf_digits = ''.join(filter(str.isdigit, cpf_str or ''))
    if not cpf_digits:
        return None
    with conexao.cursor() as cursor:
        cursor.execute("SELECT ID_PACIENTE FROM PACIENTE WHERE CPF_PACIENTE = %s", (cpf_digits,))
        row = cursor.fetchone()
        return row['ID_PACIENTE'] if row else None

def analisar_imagem_colorida(frame):
    # Escala de medidas (calibração manual)
    mm_per_pixel_x, mm_per_pixel_y = 2/63, 10/246

    # Converte para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Máscara para vermelho
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

    # Contornos da amostra
    contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours_red:
        return 0, 0  # Nenhuma amostra detectada

    # Pega o maior contorno (amostra principal)
    c_red = max(contours_red, key=cv2.contourArea)

    # Desenha o contorno da amostra em verde
    cv2.drawContours(frame, [c_red], -1, (0, 255, 0), 2)

    # Retângulo mínimo rotacionado que envolve a amostra
    rect = cv2.minAreaRect(c_red)
    box = cv2.boxPoints(rect)
    box = box.astype(int) 
    cv2.drawContours(frame, [box], 0, (0, 255, 255), 2)  # retângulo em amarelo

    # Dimensões (em pixels)
    (width_px, height_px) = rect[1]

    # Converte para mm (ajustando com calibração)
    largura_mm = round(width_px * mm_per_pixel_x, 2)
    altura_mm = round(height_px * mm_per_pixel_y, 2)

    # --- DETECÇÃO DA MARGEM (PRETA) ---
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 50])
    mask_black = cv2.inRange(hsv, lower_black, upper_black)
    contours_black, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(frame, contours_black, -1, (255, 0, 0), 2)

    # Salva imagem para uso no relatório / interação manual
    cv2.imwrite("resultado.jpg", frame)

    return largura_mm, altura_mm


def inserir_print(conexao, frame, id_usuario, largura, altura,
                  anotacao_medico, gemini_result, paciente_id=None):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captura_{timestamp}.png"
        cv2.imwrite(filename, frame)

        with open(filename, 'rb') as f:
            imagem_binaria = f.read()
        data_atual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

       
        colunas = ["IMAGEM_AMOSTRA", "ALTURA_AMOSTRA", "LARGURA_AMOSTRA",
                   "DATA_AMOSTRA", "MEDICO_USUARIO_ID_USUARIO",
                   "ANOTACAO_MEDICO_AMOSTRA", "ANOTACAO_IA_AMOSTRA"]
        valores = [imagem_binaria, altura, largura, data_atual,
                   id_usuario, anotacao_medico, gemini_result]

        if paciente_id:
            colunas.append("PACIENTE_ID_PACIENTE")
            valores.append(paciente_id)

        placeholders = ", ".join(["%s"] * len(valores))
        sql = f"INSERT INTO AMOSTRA ({', '.join(colunas)}) VALUES ({placeholders})"

        with conexao.cursor() as cursor:
            cursor.execute(sql, valores)
            conexao.commit()

        try: os.remove(filename)
        except: pass

        print("Dados da amostra inseridos com sucesso")
    except Exception as e:
        print("ERRO em inserir_print:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise

def analisar_com_gemini(largura_mm, altura_mm, observacoes):
    if not api_key:
        print("GEMINI_API_KEY não configurada. Pulando Gemini", file=sys.stderr)
        return ""
    try:
        
        prompt = (
            "Você é um assistente médico especializado em análise de imagens de microscópio.\n"
            "Com base nas seguintes medidas da amostra, forneça uma análise clínica resumida e recomendações.\n"
            f"Largura: {largura_mm:.2f} mm\n"
            f"Altura: {altura_mm:.2f} mm\n"
            f"Observações médicas: {observacoes}\n"
        )
        model = genai.GenerativeModel(model_name='gemini-2.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Falha Gemini:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return ""

def process_image_file(image_path, anotacao, gemini_obs, cpf, user_id, user_name):



    try:
        if not os.path.isfile(image_path):
            print(f"Arquivo não encontrado: {image_path}", file=sys.stderr)
            return 2

        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Não foi possível ler a imagem: {image_path}", file=sys.stderr)
            return 3


        cpf = cpf.strip().replace('.', '').replace('-', '')
        

        # ----------------- Nossa análise substituindo a antiga -----------------
        largura_mm, altura_mm = analisar_imagem_colorida(frame)
        # ----------------------------------------------------------------------

        conexao = conectar_banco()

        paciente_id = buscar_paciente_por_cpf(conexao, cpf)
        

        gemini_result = analisar_com_gemini(largura_mm, altura_mm, gemini_obs)

        inserir_print(conexao, frame, int(user_id) if user_id else None,
                      largura_mm, altura_mm, anotacao, gemini_result,
                      paciente_id=paciente_id)

        try: conexao.close()
        except: pass

        print("[process_image] processamento finalizado com sucesso")
        return 0

    except Exception as e:
        print("ERRO em process_image_file:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 10

def parse_args_and_run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True, help='Caminho para o arquivo de imagem (png/jpg)')
    parser.add_argument('--anotacao', default='')
    parser.add_argument('--gemini_obs', default='')
    parser.add_argument('--cpf', default='')
    parser.add_argument('--user-id', default='')
    parser.add_argument('--user-name', default='')
    args = parser.parse_args()
    

    rc = process_image_file(args.image, args.anotacao, args.gemini_obs,
                             args.cpf,
                            args.user_id, args.user_name)
    sys.exit(rc)

if __name__ == '__main__':
    parse_args_and_run()
