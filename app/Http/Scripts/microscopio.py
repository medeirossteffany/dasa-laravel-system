import cv2
import numpy as np
import datetime
import pymysql
import os
import argparse
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

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
        print("Conectado com sucesso")
        return conexao
    except pymysql.MySQLError as err:
        print(f"Erro ao conectar ao banco: {err}")
        exit(1)


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
    os.remove(filename)
    print("Dados da amostra inseridos no banco com sucesso.")


def analisar_com_gemini(largura_mm, altura_mm, margem_ok, observacoes, amostra_retirada):
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


class MicroscopioApp:
    def __init__(self, root, id_usuario_logado: int, nome_usuario: str):
        self.root = root
        self.root.title("Microscopio - Captura")
        self.conexao = conectar_banco()
        self.id_usuario_logado = id_usuario_logado
        self.nome_usuario = nome_usuario
        self.iniciar_camera()

    def iniciar_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.mm_per_pixel_x = 0.0723
        self.mm_per_pixel_y = 0.06696

        if hasattr(self, 'captura_frame') and self.captura_frame.winfo_exists():
            self.captura_frame.destroy()

        self.captura_frame = tk.Frame(self.root)
        self.captura_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(self.captura_frame, text=f"Profissional Saúde: {self.nome_usuario}").grid(row=0, column=0, sticky="w", pady=(0, 10))

        tk.Label(self.captura_frame, text="Observação").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.anotacao_entry = tk.Entry(self.captura_frame, width=60)
        self.anotacao_entry.grid(row=2, column=0, sticky="w", pady=(0, 15))

        tk.Label(self.captura_frame, text="Informações adicionais para análise (tipo de amostra, sintomas, etc):").grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.gemini_obs_entry = tk.Entry(self.captura_frame, width=60)
        self.gemini_obs_entry.grid(row=4, column=0, sticky="w", pady=(0, 15))

        self.amostra_retirada_var = tk.BooleanVar()
        self.amostra_checkbox = tk.Checkbutton(
            self.captura_frame,
            text="A amostra já foi retirada do paciente",
            variable=self.amostra_retirada_var,
            command=self.on_toggle_amostra
        )
        self.amostra_checkbox.grid(row=5, column=0, sticky="w", pady=(0, 8))

        self.cpf_label = tk.Label(self.captura_frame, text="CPF do paciente (somente números):")
        self.cpf_entry = tk.Entry(self.captura_frame, width=30)
        self.cpf_label.grid(row=6, column=0, sticky="w", pady=(0, 5))
        self.cpf_entry.grid(row=7, column=0, sticky="w", pady=(0, 15))
        self.cpf_label.grid_remove()
        self.cpf_entry.grid_remove()

        self.video_label = tk.Label(self.captura_frame)
        self.video_label.grid(row=0, column=1, rowspan=10, padx=(20, 0), pady=10)

        self.botoes_frame = tk.Frame(self.captura_frame)
        self.botoes_frame.grid(row=9, column=0, sticky="w", pady=10)

        self.capturar_btn = tk.Button(self.botoes_frame, text="Capturar e Salvar", width=25, height=2, command=self.capturar_e_salvar)
        self.capturar_btn.pack(side=tk.LEFT, padx=10)

        self.sair_btn = tk.Button(self.botoes_frame, text="Sair", width=25, height=2, command=self.sair)
        self.sair_btn.pack(side=tk.LEFT, padx=10)

        self.ultima_largura_mm = None
        self.ultima_altura_mm = None
        self.ultima_margem_ok = None

        self.atualizar_video()

    def on_toggle_amostra(self):
        if self.amostra_retirada_var.get():
            self.cpf_label.grid()
            self.cpf_entry.grid()
        else:
            self.cpf_label.grid_remove()
            self.cpf_entry.grid_remove()
            self.cpf_entry.delete(0, tk.END)

    def atualizar_video(self):
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Erro", "Erro ao capturar frame da câmera.")
            self.sair()
            return

        frame = frame[0:480, 0:640]
        self.frame_limpo = frame.copy()

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
        self.ultima_largura_mm = None
        self.ultima_altura_mm = None
        self.ultima_margem_ok = None  # <<< corrigido

        if contours_black:
            c_black = max(contours_black, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c_black)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            largura_mm = w * self.mm_per_pixel_x
            altura_mm = h * self.mm_per_pixel_y
            self.ultima_largura_mm = largura_mm
            self.ultima_altura_mm = altura_mm

            margem_ok = True
            margem_minima_px = int(0.2 / ((self.mm_per_pixel_x + self.mm_per_pixel_y) / 2))
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
            self.ultima_margem_ok = margem_ok

            cv2.putText(frame, f"Largura: {largura_mm:.2f} mm", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
            cv2.putText(frame, f"Altura: {altura_mm:.2f} mm", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
            status = "Margem OK (>=0.2mm)" if margem_ok else "Margem insuficiente!"
            cor_status = (0, 200, 0) if margem_ok else (0, 0, 255)
            cv2.putText(frame, status, (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_status, 2)

        frame_resized = cv2.resize(frame, (800, 600), interpolation=cv2.INTER_LINEAR)
        img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)

        self.video_label.imgtk = img_tk
        self.video_label.configure(image=img_tk)
        self.root.after(15, self.atualizar_video)

    def capturar_e_salvar(self):
        anotacao = self.anotacao_entry.get()
        gemini_obs = self.gemini_obs_entry.get()
        amostra_retirada = self.amostra_retirada_var.get()
        largura_mm = getattr(self, 'ultima_largura_mm', None)
        altura_mm = getattr(self, 'ultima_altura_mm', None)
        margem_ok = getattr(self, 'ultima_margem_ok', None)

        paciente_id = None
        if amostra_retirada:
            cpf = self.cpf_entry.get().strip()
            if not cpf:
                messagebox.showerror("CPF obrigatório", "Informe o CPF do paciente para vincular a amostra.")
                return
            self.garantir_conexao()
            paciente_id = buscar_paciente_por_cpf(self.conexao, cpf)
            if paciente_id is None:
                messagebox.showerror("Paciente não encontrado", "CPF não localizado na base de pacientes.")
                return

        gemini_result = ""
        if largura_mm and altura_mm and margem_ok is not None:
            gemini_result = analisar_com_gemini(largura_mm, altura_mm, margem_ok, gemini_obs, amostra_retirada)
            # messagebox.showinfo("Análise Gemini", gemini_result)
        # else:
        #     messagebox.showwarning("Análise Gemini", "Dados insuficientes para análise automática.")

        messagebox.showinfo("Captura", "Imagem capturada e salva com sucesso!")
        self.garantir_conexao()
        inserir_print(
            self.conexao,
            self.frame_limpo,
            self.id_usuario_logado,
            self.mm_per_pixel_x,
            self.mm_per_pixel_y,
            anotacao,
            gemini_result,
            paciente_id=paciente_id
        )
        self.anotacao_entry.delete(0, tk.END)
        self.gemini_obs_entry.delete(0, tk.END)
        self.amostra_retirada_var.set(False)
        self.on_toggle_amostra()

    def garantir_conexao(self):
        try:
            self.conexao.ping(reconnect=True)
        except:
            self.conexao = conectar_banco()

    def sair(self):
        if hasattr(self, 'cap'):
            self.cap.release()
        self.conexao.close()
        self.root.destroy()


def parse_user():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, help="ID do usuário autenticado")
    parser.add_argument("--user-name", type=str, help="Nome do usuário autenticado")
    args = parser.parse_args()

    user_id = args.user_id or os.getenv("AUTH_USER_ID")
    user_name = args.user_name or os.getenv("AUTH_USER_NAME")

    if user_id is None or str(user_id).strip() == "":
        return None, None
    try:
        user_id = int(user_id)
    except ValueError:
        return None, None
    if not user_name:
        user_name = f"Usuario {user_id}"
    return user_id, user_name


def main():
    user_id, user_name = parse_user()
    if user_id is None:
        print("Erro: passe --user-id/--user-name ou defina AUTH_USER_ID/AUTH_USER_NAME no ambiente.")
        return

    root = tk.Tk()
    root.geometry("1000x800")
    app = MicroscopioApp(root, user_id, user_name)
    root.protocol("WM_DELETE_WINDOW", app.sair)
    root.mainloop()


if __name__ == "__main__":
    main()
