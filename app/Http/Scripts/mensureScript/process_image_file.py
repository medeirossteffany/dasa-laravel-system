import os
import traceback
import cv2
import sys
from conectar_banco import conectar_banco, buscar_paciente_por_cpf
from analisar_imagem_medicao import analisar_imagem_colorida
from analise_gemini import analisar_com_gemini
from inserir_print import inserir_print


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
        largura_mm, altura_mm, frame = analisar_imagem_colorida(frame)
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