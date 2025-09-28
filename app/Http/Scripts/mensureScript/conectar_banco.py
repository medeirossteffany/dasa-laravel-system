import pymysql
from dotenv import load_dotenv
import os
import google.generativeai as genai
import sys

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
