import datetime
import cv2
import numpy as np


def inserir_print(conexao, frame_limpo, id_usuario_logado, mm_per_pixel_x, mm_per_pixel_y, anotacao_medico, gemini_result, paciente_id):
    # Converter o frame diretamente para PNG em memória (sem salvar localmente)
    _, buffer = cv2.imencode(".png", frame_limpo)
    imagem_binaria = buffer.tobytes()
    print("[✔] Imagem preparada para inserção no banco")

    # Pré-processamento para encontrar contornos
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
        if mmX < 2 or mmY < 2:  # ignora objetos muito pequenos
            continue
        larguras.append(mmX)
        alturas.append(mmY)

    # Ordena para pegar a segunda maior medida
    larguras.sort(reverse=True)
    alturas.sort(reverse=True)
    segunda_largura = round(larguras[1] if len(larguras) > 1 else (larguras[0] if larguras else 0), 2)
    segunda_altura = round(alturas[1] if len(alturas) > 1 else (alturas[0] if alturas else 0), 2)

    print(f"Segunda maior largura detectada: {segunda_largura:.2f} mm")
    print(f"Segunda maior altura detectada: {segunda_altura:.2f} mm")

    data_atual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Inserção no banco
    try:
        with conexao.cursor() as cursor:
            sql = """INSERT INTO AMOSTRA (
                        IMAGEM_AMOSTRA, ALTURA_AMOSTRA, LARGURA_AMOSTRA, DATA_AMOSTRA, 
                        MEDICO_USUARIO_ID_USUARIO, ANOTACAO_MEDICO_AMOSTRA, ANOTACAO_IA_AMOSTRA, PACIENTE_ID_PACIENTE
                     )
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            valores = (imagem_binaria, segunda_altura, segunda_largura, data_atual,
                       id_usuario_logado, anotacao_medico, gemini_result, paciente_id)
            cursor.execute(sql, valores)
            conexao.commit()
        print("[✔] Dados da amostra inseridos no banco com sucesso.")
    except Exception as e:
        print(f"[❌] Erro ao inserir dados no banco: {e}")
        conexao.rollback()
