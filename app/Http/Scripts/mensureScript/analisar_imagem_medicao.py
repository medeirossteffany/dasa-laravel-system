import cv2
import numpy as np

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