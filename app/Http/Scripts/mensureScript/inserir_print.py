import datetime
import cv2
import traceback
import sys
import os

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
