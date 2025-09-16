import customtkinter as ctk

from models.MicroscopioApp import MicroscopioApp


def main():
    root = ctk.CTk()
    root.geometry("1000x800")
    app = MicroscopioApp(root)
    root.protocol("WM_DELETE_WINDOW", app.sair)
    root.mainloop()


if __name__ == "__main__":
    main()
