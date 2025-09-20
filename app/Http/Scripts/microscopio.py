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

def inserir_print(conexao, frame, id_usuario, mm_per_pixel_x, mm_per_pixel_y,
                  anotacao_medico, gemini_result, paciente_id=None):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captura_{timestamp}.png"
        cv2.imwrite(filename, frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        eroded = cv2.erode(threshold, kernel, iterations=1)
        contours, _ = cv2.findContours(eroded, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        larguras, alturas = [], []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            mmX, mmY = w*mm_per_pixel_x, h*mm_per_pixel_y
            if mmX < 2 or mmY < 2:
                continue
            larguras.append(mmX)
            alturas.append(mmY)

        larguras.sort(reverse=True)
        alturas.sort(reverse=True)
        segunda_largura = round(larguras[1] if len(larguras) > 1 else (larguras[0] if larguras else 0), 2)
        segunda_altura = round(alturas[1] if len(alturas) > 1 else (alturas[0] if alturas else 0), 2)

        with open(filename, 'rb') as f:
            imagem_binaria = f.read()
        data_atual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        colunas = ["IMAGEM_AMOSTRA", "ALTURA_AMOSTRA", "LARGURA_AMOSTRA",
                   "DATA_AMOSTRA", "MEDICO_USUARIO_ID_USUARIO",
                   "ANOTACAO_MEDICO_AMOSTRA", "ANOTACAO_IA_AMOSTRA"]
        valores = [imagem_binaria, segunda_altura, segunda_largura, data_atual,
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

def analisar_com_gemini(largura_mm, altura_mm, margem_ok, observacoes, amostra_retirada):
    if not api_key:
        print("GEMINI_API_KEY não configurada. Pulando Gemini", file=sys.stderr)
        return ""
    try:
        local = "Análise em amostra retirada do paciente" if amostra_retirada else "Análise direta no corpo do paciente"
        margem_texto = f"- Margem: {'OK' if margem_ok else 'Insuficiente'}\n" if amostra_retirada else ""
        prompt = (
            f"{local}\n"
            f"Largura: {largura_mm:.2f} mm\n"
            f"Altura: {altura_mm:.2f} mm\n"
            f"{margem_texto}"
            f"Observações médicas: {observacoes}\n"
            "Forneça análise clínica resumida e recomendações."
        )
        model = genai.GenerativeModel(model_name='gemini-2.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Falha Gemini:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return ""

def process_image_file(image_path, anotacao, gemini_obs, amostra_retirada_flag, cpf, user_id, user_name):
    try:
        if not os.path.isfile(image_path):
            print(f"Arquivo não encontrado: {image_path}", file=sys.stderr)
            return 2

        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Não foi possível ler a imagem: {image_path}", file=sys.stderr)
            return 3

        mm_per_pixel_x, mm_per_pixel_y = 0.0265, 0.0291

        # ----------------- Lógica do segundo código adaptada -----------------
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 60])
        mask_black = cv2.inRange(hsv, lower_black, upper_black)

        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 50])
        upper_red2 = np.array([180, 255, 255])
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

        contours_black, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours_black:
            c_black = max(contours_black, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c_black)

            largura_mm = w * mm_per_pixel_x
            altura_mm = h * mm_per_pixel_y

            # Margem mínima 0.2 mm
            margem_ok = True
            margem_minima_px = int(0.2 / ((mm_per_pixel_x + mm_per_pixel_y) / 2))
            x_exp = max(0, x - margem_minima_px)
            y_exp = max(0, y - margem_minima_px)
            w_exp = min(frame.shape[1] - x_exp, w + 2 * margem_minima_px)
            h_exp = min(frame.shape[0] - y_exp, h + 2 * margem_minima_px)
            roi_margem = mask_red[y_exp:y_exp + h_exp, x_exp:x_exp + w_exp]
            borda_superior = roi_margem[0:margem_minima_px, :]
            borda_inferior = roi_margem[-margem_minima_px:, :]
            borda_esquerda = roi_margem[:, 0:margem_minima_px]
            borda_direita = roi_margem[:, -margem_minima_px:]
            if (cv2.countNonZero(borda_superior) == 0 or
                cv2.countNonZero(borda_inferior) == 0 or
                cv2.countNonZero(borda_esquerda) == 0 or
                cv2.countNonZero(borda_direita) == 0):
                margem_ok = False
        else:
            largura_mm, altura_mm, margem_ok = 0, 0, False
        # ----------------------------------------------------------------------

        conexao = conectar_banco()
        paciente_id = buscar_paciente_por_cpf(conexao, cpf) if amostra_retirada_flag and cpf else None

        gemini_result = analisar_com_gemini(largura_mm, altura_mm, margem_ok, gemini_obs, amostra_retirada_flag)

        inserir_print(conexao, frame, int(user_id) if user_id else None,
                      mm_per_pixel_x, mm_per_pixel_y, anotacao, gemini_result,
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
    parser.add_argument('--amostra_retirada', default='0')
    parser.add_argument('--cpf', default='')
    parser.add_argument('--user-id', default='')
    parser.add_argument('--user-name', default='')
    args = parser.parse_args()

    rc = process_image_file(args.image, args.anotacao, args.gemini_obs,
                            args.amostra_retirada=='1', args.cpf,
                            args.user_id, args.user_name)
    sys.exit(rc)

if __name__ == '__main__':
    parse_args_and_run()
