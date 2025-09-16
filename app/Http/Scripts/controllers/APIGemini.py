import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def analisar_com_gemini(largura_mm, altura_mm, margem_ok, observacoes, amostra_retirada):
    if amostra_retirada:
        local_analise = "A análise está sendo feita em uma amostra já retirada do paciente."
        margem_texto = f"- Margem de remoção: {'OK (>=0.2mm)' if margem_ok else 'Insuficiente (<0.2mm)'}\n"
    else:
        local_analise = "A análise está sendo feita diretamente no corpo do paciente."
        margem_texto = ""  # Não inclui margem no prompt

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