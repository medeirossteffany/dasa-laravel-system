import cv2
import numpy as np

def analisar_imagem_colorida(frame, salvar_resultado=True, caminho_saida="resultado_para_profissional.jpg"):
    # Redimensiona para 640x480
    frame = cv2.resize(frame, (640, 480))
    
    # Calibração mm/pixel (ajuste conforme sua régua)
    mm_per_pixel_x, mm_per_pixel_y = 1.8/70, 10/301  

    # Convertendo para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Segmentação melhorada de pele clara e média
    lower_skin1 = np.array([0, 10, 60])
    upper_skin1 = np.array([20, 150, 255])
    
    lower_skin2 = np.array([160, 10, 60])
    upper_skin2 = np.array([179, 150, 255])
    
    mask_skin1 = cv2.inRange(hsv, lower_skin1, upper_skin1)
    mask_skin2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
    
    mask_skin = cv2.bitwise_or(mask_skin1, mask_skin2)

    # Invertendo máscara de pele para focar na amostra
    mask_sample = cv2.bitwise_not(mask_skin)

    # Limpeza de ruído
    kernel = np.ones((5,5), np.uint8)
    mask_sample = cv2.morphologyEx(mask_sample, cv2.MORPH_CLOSE, kernel)
    mask_sample = cv2.morphologyEx(mask_sample, cv2.MORPH_OPEN, kernel)
    
    # Detecção de contornos
    contours, _ = cv2.findContours(mask_sample, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        
        return None, None
    
    # Selecionar o contorno maior
    c = max(contours, key=cv2.contourArea)
    
    # Filtrar contornos muito pequenos
    if cv2.contourArea(c) < 500:
        
        return None, None
    
    x, y, w, h = cv2.boundingRect(c)
    
    mmx = round(w * mm_per_pixel_x, 2)
    mmy = round(h * mm_per_pixel_y, 2)
    
    # Desenhar contorno e retângulo na amostra detectada
    cv2.drawContours(frame, [c], -1, (0, 0, 255), 2)  # contorno em vermelho
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # retângulo em azul
    cv2.putText(frame, f"L: {mmx} mm", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"A: {mmy} mm", (x, y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Salvar imagem com resultado
    if salvar_resultado:
        cv2.imwrite(caminho_saida, frame)
        
    return mmx, mmy, frame