import cv2
import numpy as np
import datetime
import pymysql
import os
import argparse
import sys
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import google.generativeai as genai
from pathlib import Path
import traceback

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


def inserir_print(conexao, frame_limpo, id_usuario_logado, mm_per_pixel_x, mm_per_pixel_y,
                  anotacao_medico, gemini_result, paciente_id=None):
    """
    Salva a imagem temporariamente, calcula contornos e tamanhos, grava binário no banco.
    Usa a mesma lógica que você já tinha.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captura_{timestamp}.png"
        cv2.imwrite(filename, frame_limpo)
        print(f"[✔] Imagem salva como: {filename}")

        gray = cv2.cvtColor(frame_limpo, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        eroded = cv2.erode(threshold, kernel, iterations=1)
        contours, _ = cv2.findContours(eroded, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        larguras, alturas = [], []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            mmX = w * mm_per_pixel_x
            mmY = h * mm_per_pixel_y
            if mmX < 2 or mmY < 2:
                continue
            larguras.append(mmX)
            alturas.append(mmY)

        larguras.sort(reverse=True)
        alturas.sort(reverse=True)
        segunda_largura = round(larguras[1] if len(larguras) > 1 else (larguras[0] if larguras else 0), 2)
        segunda_altura = round(alturas[1] if len(alturas) > 1 else (alturas[0] if alturas else 0), 2)

        print(f"Segunda maior largura detectada: {segunda_largura:.2f} mm")
        print(f"Segunda maior altura detectada: {segunda_altura:.2f} mm")

        with open(filename, 'rb') as file:
            imagem_binaria = file.read()
        data_atual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        colunas = [
            "IMAGEM_AMOSTRA",
            "ALTURA_AMOSTRA",
            "LARGURA_AMOSTRA",
            "DATA_AMOSTRA",
            "MEDICO_USUARIO_ID_USUARIO",
            "ANOTACAO_MEDICO_AMOSTRA",
            "ANOTACAO_IA_AMOSTRA",
        ]
        valores = [
            imagem_binaria,
            segunda_altura,
            segunda_largura,
            data_atual,
            id_usuario_logado,
            anotacao_medico,
            gemini_result,
        ]

        if paciente_id is not None:
            colunas.append("PACIENTE_ID_PACIENTE")
            valores.append(paciente_id)

        placeholders = ", ".join(["%s"] * len(valores))
        sql = f"INSERT INTO AMOSTRA ({', '.join(colunas)}) VALUES ({placeholders})"

        with conexao.cursor() as cursor:
            cursor.execute(sql, valores)
            conexao.commit()
        try:
            os.remove(filename)
        except Exception:
            pass
        print("Dados da amostra inseridos no banco com sucesso.")
    except Exception as e:
        print("ERRO em inserir_print:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise


def analisar_com_gemini(largura_mm, altura_mm, margem_ok, observacoes, amostra_retirada):
    """
    Gera texto via Gemini — pode falhar se não tiver chave; lidamos com exceção.
    """
    if not api_key:
        print("Aviso: GEMINI_API_KEY não configurada. Pulando chamada Gemini.", file=sys.stderr)
        return ""
    try:
        if amostra_retirada:
            local_analise = "A análise está sendo feita em uma amostra já retirada do paciente."
            margem_texto = f"- Margem de remoção: {'OK (>=0.2mm)' if margem_ok else 'Insuficiente (<0.2mm)'}\n"
        else:
            local_analise = "A análise está sendo feita diretamente no corpo do paciente."
            margem_texto = ""
        prompt = (
            f"{local_analise}\n"
            f"Analise uma amostra microscópica com as seguintes características:\n"
            f"- Largura: {largura_mm:.2f} mm\n"
            f"- Altura: {altura_mm:.2f} mm\n"
            f"{margem_texto}"
            f"- Observações do médico: {observacoes}\n"
            f"Com base nesses dados, forneça uma análise clínica resumida e recomendações."
        )
        model = genai.GenerativeModel(model_name='gemini-2.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Aviso: erro ao chamar Gemini:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return ""

# ---------------- Processamento ----------------

def process_image_file(image_path, anotacao, gemini_obs, amostra_retirada_flag, cpf, user_id, user_name):
    """
    Processa a imagem que já está salva no disco:
    - lê a imagem
    - roda análise (contornos, medidas)
    - chama Gemini (opcional)
    - grava no banco usando inserir_print
    Retorna código de saída (0 sucesso, >0 erro).
    """
    try:
        image_path = str(image_path)
        if not os.path.isfile(image_path):
            print(f"ERRO: arquivo não encontrado: {image_path}", file=sys.stderr)
            return 2

        frame = cv2.imread(image_path)
        if frame is None:
            print(f"ERRO: não foi possível ler imagem {image_path}", file=sys.stderr)
            return 3

        # parâmetros mm/pixel
        mm_per_pixel_x = 0.0723
        mm_per_pixel_y = 0.06696

        # processamento (similar ao inserir_print, mas sem regravar arquivo para não duplicar)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        eroded = cv2.erode(threshold, kernel, iterations=1)
        contours, _ = cv2.findContours(eroded, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        larguras, alturas = [], []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            mmX = w * mm_per_pixel_x
            mmY = h * mm_per_pixel_y
            if mmX < 2 or mmY < 2:
                continue
            larguras.append(mmX)
            alturas.append(mmY)
        larguras.sort(reverse=True)
        alturas.sort(reverse=True)
        segunda_largura = round(larguras[1] if len(larguras) > 1 else (larguras[0] if larguras else 0), 2)
        segunda_altura = round(alturas[1] if len(alturas) > 1 else (alturas[0] if alturas else 0), 2)
        print(f"[process_image] segunda_largura={segunda_largura}, segunda_altura={segunda_altura}")

        # heurística simples de margem_ok (pode adaptar)
        margem_ok = bool(segunda_largura > 0 and segunda_altura > 0)

        conexao = conectar_banco()
        paciente_id = None
        if amostra_retirada_flag and cpf:
            try:
                paciente_id = buscar_paciente_por_cpf(conexao, cpf)
            except Exception as e:
                print("Aviso: falha ao buscar paciente por CPF:", e, file=sys.stderr)

        gemini_result = ""
        try:
            if segunda_largura and segunda_altura:
                gemini_result = analisar_com_gemini(segunda_largura, segunda_altura, margem_ok, gemini_obs, amostra_retirada_flag)
        except Exception as e:
            print("Aviso: falha ao chamar Gemini:", e, file=sys.stderr)

        # Inserir na base com a função existente (que salva a imagem em arquivo temporário, lê como binário e remove)
        inserir_print(conexao, frame, int(user_id) if user_id else None, mm_per_pixel_x, mm_per_pixel_y, anotacao, gemini_result, paciente_id=paciente_id)
        try:
            conexao.close()
        except Exception:
            pass

        print("[process_image] processamento finalizado com sucesso")
        return 0

    except Exception as e:
        print("ERRO em process_image_file:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 10


# ---------------- Argument parser e pontes ----------------

def parse_args_and_run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', help='Caminho para o arquivo de imagem (png/jpg)')
    parser.add_argument('--anotacao', default='')
    parser.add_argument('--gemini_obs', default='')
    parser.add_argument('--amostra_retirada', default='0')
    parser.add_argument('--cpf', default='')
    parser.add_argument('--user-id', default='')
    parser.add_argument('--user-name', default='')
    args = parser.parse_args()

    if args.image:
        # run in headless processing mode
        rc = process_image_file(args.image, args.anotacao, args.gemini_obs, args.amostra_retirada == '1', args.cpf, args.user_id, args.user_name)
        sys.exit(rc)
    else:
        # No image param -> open GUI (local)
        user_id = None
        user_name = None
        # if provided user args but no image, use them
        if args.user_id:
            try:
                user_id = int(args.user_id)
            except Exception:
                user_id = None
        if args.user_name:
            user_name = args.user_name

        # If no user info, try from env
        if user_id is None:
            try:
                env_uid = os.getenv('AUTH_USER_ID')
                if env_uid:
                    user_id = int(env_uid)
            except Exception:
                pass
        if not user_name:
            user_name = os.getenv('AUTH_USER_NAME', f'Usuario {user_id or ""}')

        root = tk.Tk()
        root.geometry("1000x800")
        app = MicroscopioApp(root, user_id, user_name)
        root.protocol("WM_DELETE_WINDOW", app.sair)
        try:
            root.mainloop()
        except KeyboardInterrupt:
            app.sair()


# ---------------- main ----------------

if __name__ == '__main__':
    parse_args_and_run()
