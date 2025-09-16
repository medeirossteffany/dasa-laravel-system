import customtkinter as ctk
from tkinter import messagebox
import threading
import cv2
import numpy as np
from PIL import Image
from controllers.APIGemini import analisar_com_gemini
from controllers.Inserir_print import inserir_print
from controllers.Login import fazer_login
from providers.DataBaseConnection import conectar_banco

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")  # paleta DASA

class MicroscopioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Microscópio DASA")
        self.root.geometry("1100x800")
        self.root.resizable(False, False)
        self.conexao = conectar_banco()
        self.id_usuario_logado = None
        self.nome_usuario = None

        # Fundo escurecido para login
        self.bg_frame = ctk.CTkFrame(root, fg_color="#f2f4f8", width=1100, height=800)
        self.bg_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Título DASA grande fora do card
        self.dasa_title = ctk.CTkLabel(self.bg_frame, text="DASA", font=ctk.CTkFont(size=64, weight="bold"), text_color="#0056b3")
        self.dasa_title.place(relx=0.5, rely=0.22, anchor="center")

        # Frame de Login (card central)
        self.login_frame = ctk.CTkFrame(self.bg_frame, corner_radius=20, width=420, height=380, fg_color="#ffffff")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.login_frame, text="Login", font=ctk.CTkFont(size=24, weight="bold"), text_color="#222").pack(pady=(30, 20))

        self.email_entry = ctk.CTkEntry(self.login_frame, placeholder_text="E-mail", width=320, height=40, font=ctk.CTkFont(size=16))
        self.email_entry.pack(pady=(10, 10), padx=30)
        self.senha_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Senha", width=320, height=40, show="*", font=ctk.CTkFont(size=16))
        self.senha_entry.pack(pady=(0, 20), padx=30)

        self.login_btn = ctk.CTkButton(
            self.login_frame, text="Entrar", width=200, height=45,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#0056b3", hover_color="#003d80", text_color="#fff",
            corner_radius=12, command=self.tentar_login
        )
        self.login_btn.pack(pady=(10, 10), padx=30)

    def tentar_login(self):
        email = self.email_entry.get()
        senha = self.senha_entry.get()
        id_usuario, nome_usuario = fazer_login(self.conexao, email, senha)
        if id_usuario:
            self.id_usuario_logado = id_usuario
            self.nome_usuario = nome_usuario
            messagebox.showinfo("Login", f"Bem-vindo, {nome_usuario}!")
            self.bg_frame.destroy()
            self.dasa_title.destroy()
            self.login_frame.destroy()
            self.iniciar_camera()
        else:
            messagebox.showerror("Erro", "E-mail ou senha incorretos.")

    def iniciar_camera(self):
        self.root.title("Microscópio DASA - Captura")
        self.cap = cv2.VideoCapture(0)
        self.mm_per_pixel_x = 0.0723
        self.mm_per_pixel_y = 0.06696

        # Frame principal de captura
        self.captura_frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color="#f2f4f8")
        self.captura_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Coluna esquerda: campos e botões
        self.campos_frame = ctk.CTkFrame(self.captura_frame, corner_radius=15, width=370, fg_color="#fff")
        self.campos_frame.grid(row=0, column=0, padx=30, pady=30, sticky="n")

        # Campo para selecionar paciente por ID
        ctk.CTkLabel(self.campos_frame, text="ID do Paciente:", anchor="w", font=ctk.CTkFont(size=16)).pack(pady=(10,5), padx=20, fill="x")
        self.paciente_id_entry = ctk.CTkEntry(
            self.campos_frame,
            placeholder_text="Digite o ID do paciente",
            width=340,
            font=ctk.CTkFont(size=15)
        )
        self.paciente_id_entry.pack(pady=(0,15), padx=20, fill="x")

        ctk.CTkLabel(self.campos_frame, text="Observação do médico:", anchor="w", font=ctk.CTkFont(size=16)).pack(pady=(0,5), padx=20, fill="x")
        self.anotacao_entry = ctk.CTkTextbox(
            self.campos_frame,
            width=340,
            height=120,
            font=ctk.CTkFont(size=15),
            corner_radius=8
        )
        self.anotacao_entry.pack(pady=(0,15), padx=20, fill="x")

        ctk.CTkLabel(self.campos_frame, text="Informações adicionais para análise:", anchor="w", font=ctk.CTkFont(size=16)).pack(pady=(0,5), padx=20, fill="x")
        self.gemini_obs_entry = ctk.CTkTextbox(
            self.campos_frame,
            width=340,
            height=120,
            font=ctk.CTkFont(size=15),
            corner_radius=8
        )
        self.gemini_obs_entry.pack(pady=(0,15), padx=20, fill="x")

        self.amostra_retirada_var = ctk.BooleanVar()
        self.amostra_checkbox = ctk.CTkCheckBox(
            self.campos_frame,
            text="A amostra já foi retirada do paciente",
            variable=self.amostra_retirada_var,
            font=ctk.CTkFont(size=15)
        )
        self.amostra_checkbox.pack(pady=(0,15), padx=20, anchor="w")

        # Botões
        self.botoes_frame = ctk.CTkFrame(self.campos_frame, corner_radius=10, fg_color="#f2f4f8")
        self.botoes_frame.pack(pady=10, padx=20, fill="x")

        self.capturar_btn = ctk.CTkButton(
            self.botoes_frame, text="Capturar e Salvar",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#0056b3", hover_color="#003d80", text_color="#fff",
            corner_radius=10, command=self.capturar_e_salvar
        )
        self.capturar_btn.pack(side="left", expand=True, padx=10, pady=10)
        self.sair_btn = ctk.CTkButton(
            self.botoes_frame, text="Sair",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#e74c3c", hover_color="#c0392b", text_color="#fff",
            corner_radius=10, command=self.sair
        )
        self.sair_btn.pack(side="left", expand=True, padx=10, pady=10)

        # Coluna direita: vídeo
        self.video_frame = ctk.CTkFrame(self.captura_frame, corner_radius=15, width=640, height=480, fg_color="#fff")
        self.video_frame.grid(row=0, column=1, padx=30, pady=30)
        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        self.video_label.pack(padx=10, pady=10)

        # Ajuste de grid
        self.captura_frame.grid_columnconfigure(0, weight=1)
        self.captura_frame.grid_columnconfigure(1, weight=1)

        self.atualizar_video()

    def atualizar_video(self):
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Erro", "Erro ao capturar frame da câmera.")
            self.sair()
            return

        # Ajuste para 640x480
        frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)
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
        self.ultima_margem_ok = None
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

            cv2.putText(frame, f"Largura: {largura_mm:.2f} mm", (15, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
            cv2.putText(frame, f"Altura: {altura_mm:.2f} mm", (15, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
            status = "Margem OK (>=0.2mm)" if margem_ok else "Margem insuficiente!"
            cor_status = (0, 200, 0) if margem_ok else (0, 0, 255)
            cv2.putText(frame, status, (15, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_status, 2)

        # Exibe vídeo no tamanho correto usando CTkImage
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_ctk = ctk.CTkImage(light_image=img_pil, size=(640, 480))
        self.video_label.configure(image=img_ctk)
        self.video_label.image = img_ctk  # Evita garbage collection
        self.root.after(15, self.atualizar_video)

    def capturar_e_salvar(self):
        # Animação de carregamento
        self.loading = True
        self.loading_frame = ctk.CTkFrame(self.root, fg_color="#000000", corner_radius=15)
        self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Salvando...", font=ctk.CTkFont(size=22, weight="bold"))
        self.loading_label.pack(padx=40, pady=30)
        self.loading_anim_label = ctk.CTkLabel(self.loading_frame, text="", font=ctk.CTkFont(size=32, weight="bold"))
        self.loading_anim_label.pack(pady=(0, 30))
        self.loading_anim_index = 0
        self.animate_loading()

        def salvar():
            paciente_id = self.paciente_id_entry.get().strip()
            anotacao = self.anotacao_entry.get("1.0", "end").strip()
            gemini_obs = self.gemini_obs_entry.get("1.0", "end").strip()
            amostra_retirada = self.amostra_retirada_var.get()
            largura_mm = getattr(self, 'ultima_largura_mm', None)
            altura_mm = getattr(self, 'ultima_altura_mm', None)
            margem_ok = getattr(self, 'ultima_margem_ok', None)
            gemini_result = ""
            if largura_mm and altura_mm and margem_ok is not None:
                gemini_result = analisar_com_gemini(largura_mm, altura_mm, margem_ok, gemini_obs, amostra_retirada)
            self.garantir_conexao()
            # Adicione paciente_id como argumento se necessário no inserir_print
            inserir_print(self.conexao, self.frame_limpo, self.id_usuario_logado,
                          self.mm_per_pixel_x, self.mm_per_pixel_y, anotacao, gemini_result, paciente_id)
            self.anotacao_entry.delete("1.0", "end")
            self.gemini_obs_entry.delete("1.0", "end")
            self.amostra_retirada_var.set(False)
            self.paciente_id_entry.delete(0, "end")
            self.loading = False
            self.loading_frame.destroy()
            messagebox.showinfo("Captura", "Imagem capturada e salva com sucesso!")

        threading.Thread(target=salvar).start()

    def animate_loading(self):
        if not hasattr(self, "loading") or not self.loading:
            return
        anim = ["⏳", "⌛", "⏳", "⌛"]
        self.loading_anim_label.configure(text=anim[self.loading_anim_index % len(anim)])
        self.loading_anim_index += 1
        self.root.after(400, self.animate_loading)

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
