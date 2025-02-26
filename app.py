import streamlit as st
import requests
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

# Configuración de la API de Gemini
API_KEY = st.secrets.get("GEMINI_API_KEY", "tu_clave_aqui")  # Usar secrets en Streamlit Cloud
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Título y estilo
st.title("BioLab Insights")
st.markdown("Analiza datos bioquímicos y haz preguntas con IA avanzada.")

# Área de entrada de datos
input_data = st.text_area(
    "Pega tus datos bioquímicos aquí",
    placeholder="Ejemplo: Glucosa: 120 mg/dL\nColesterol: 200 mg/dL",
    height=150
)

# Campo para preguntas
question = st.text_input(
    "Haz una pregunta",
    placeholder="Ejemplo: ¿Qué significa un nivel alto de glucosa?"
)

# Función para llamar a la API de Gemini
def call_gemini(text):
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "temperature": 1,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "text/plain"
        }
    }
    response = requests.post(f"{API_URL}?key={API_KEY}", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Error: {response.status_code} - {response.text}"

# Botones y lógica
col1, col2 = st.columns(2)
with col1:
    analyze_btn = st.button("Analizar Datos", disabled=not input_data)
with col2:
    ask_btn = st.button("Preguntar", disabled=not question)

# Estado para resultados
if "response" not in st.session_state:
    st.session_state.response = ""
if "chart_data" not in st.session_state:
    st.session_state.chart_data = None

# Lógica de análisis
if analyze_btn:
    with st.spinner("Analizando datos..."):
        st.session_state.response = call_gemini(input_data)
        
        # Parsear datos para gráfico
        labels = []
        values = []
        for line in input_data.split("\n"):
            if ":" in line:
                label, value = line.split(":", 1)
                try:
                    values.append(float(value.strip().split()[0]))
                    labels.append(label.strip())
                except ValueError:
                    pass
        
        if labels and values:
            df = pd.DataFrame({"Parámetro": labels, "Valor": values})
            fig, ax = plt.subplots(figsize=(8, 4))
            df.plot(kind="bar", x="Parámetro", y="Valor", ax=ax, color="#36A2EB")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.session_state.chart_data = fig

# Lógica de preguntas
if ask_btn:
    with st.spinner("Procesando pregunta..."):
        st.session_state.response = call_gemini(question)

# Mostrar resultados
if st.session_state.response:
    st.subheader("Resultado")
    st.write(st.session_state.response)
    
    # Botón de exportación a PDF
    buffer = BytesIO()
    with open("result.txt", "w") as f:
        f.write(st.session_state.response)
    with open("result.txt", "rb") as f:
        st.download_button(
            label="Exportar a TXT",
            data=f,
            file_name="analisis_biolab.txt",
            mime="text/plain"
        )

# Mostrar gráfico
if st.session_state.chart_data:
    st.subheader("Gráfico de Datos")
    st.pyplot(st.session_state.chart_data)

# Footer
st.markdown("---")
st.caption("Powered by Gemini 2.0 Flash | © 2025 BioLab Insights")
