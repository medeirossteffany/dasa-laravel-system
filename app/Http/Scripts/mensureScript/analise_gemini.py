import google.generativeai as genai
import traceback
import sys
from conectar_banco import api_key

def analisar_com_gemini(largura_mm, altura_mm, observacoes):
    if not api_key:
        print("GEMINI_API_KEY não configurada. Pulando Gemini", file=sys.stderr)
        return ""
    try:
        
        prompt = (
            "Você é um assistente médico especializado em análise de imagens de microscópio.\n"
            "Com base nas seguintes medidas da amostra, forneça uma análise clínica resumida e recomendações.\n"
            f"Largura: {largura_mm:.2f} mm\n"
            f"Altura: {altura_mm:.2f} mm\n"
            f"Observações médicas: {observacoes}\n"
        )
        model = genai.GenerativeModel(model_name='gemini-2.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Falha Gemini:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return ""

