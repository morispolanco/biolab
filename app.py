import streamlit as st
import os
import json
import base64
import requests

# Configuración de la API (ajusta según tu implementación)
API_KEY = "TU_CLAVE_API"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Estado de la sesión
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Función para analizar archivos
def analyze_files(files, analysis_type, notes, lang):
    file_info = []
    for file in files:
        if isinstance(file, str):  # Ruta de archivo local (demo)
            with open(file, "rb") as f:
                content = f.read()
            name = os.path.basename(file)
            file_type = "text/csv"  # Suponemos CSV para el demo
        else:  # Archivo subido por el usuario
            content = file.read()
            name = file.name
            file_type = file.type

        # Procesar contenido
        if file_type.startswith("image"):
            content = base64.b64encode(content).decode("utf-8")[:1000]
        else:
            content = content.decode("utf-8", errors="ignore")[:1000]
        file_info.append({"name": name, "type": file_type, "content": content})

    # Crear el prompt para la API
    prompt = f"""Analiza estos archivos bioquímicos: {json.dumps(file_info)}. 
    Tipo de análisis: {analysis_type.lower()}. Notas: {notes}. Responde en {lang}.
    Devuelve un JSON con: summary, findings, chartData, anomalies, recommendations."""

    # Llamada a la API (ajusta según tu endpoint)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "text/plain"}
    }
    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=payload)
    if response.status_code != 200:
        raise Exception(f"Error en la API: {response.text}")
    return json.loads(response.text)

# Función para mostrar resultados (ajusta según tu diseño)
def display_results(data, texts, lang):
    st.header(texts["results"])
    st.write(data["summary"])
    # Agrega más visualizaciones según tu implementación

# Aplicación principal
def main():
    lang = "es"  # Idioma por defecto, ajusta si tienes selección de idioma
    texts = {
        "title": "BioChem Assistant - Analizador de Informes Bioquímicos con IA",
        "upload": "Subir Datos",
        "analyze": "Analizar Datos",
        "results": "Resultados del Análisis",
        "demo_header": "Demo",
        "demo_description": "Haz clic abajo para ejecutar un análisis con datos de muestra.",
        "demo_btn": "Ejecutar Análisis de Demostración",
        "error": "Error al procesar la solicitud"
    }

    st.title(texts["title"])

    # Subida de archivos
    st.sidebar.header(texts["upload"])
    uploaded_files = st.sidebar.file_uploader("Archivos", type=["csv", "txt", "pdf", "jpg"], accept_multiple_files=True)
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files

    analyze_btn = st.sidebar.button(texts["analyze"], disabled=not st.session_state.uploaded_files)

    # Sección de demo
    st.sidebar.header(texts["demo_header"])
    st.sidebar.write(texts["demo_description"])
    if st.sidebar.button(texts["demo_btn"]):
        with st.spinner("Ejecutando análisis de demostración..."):
            try:
                sample_file = "sample_data.csv"
                if not os.path.exists(sample_file):
                    st.error("Archivo de muestra no encontrado. Asegúrate de que 'sample_data.csv' esté en el repositorio.")
                    return
                analysis_data = analyze_files([sample_file], "General", "", lang)
                st.session_state.analysis_data = analysis_data
                display_results(analysis_data, texts, lang)
            except Exception as e:
                st.error(f"Error en el demo: {str(e)}")

    # Análisis de archivos subidos
    if analyze_btn and st.session_state.uploaded_files:
        with st.spinner("Analizando datos..."):
            try:
                analysis_data = analyze_files(st.session_state.uploaded_files, "General", "", lang)
                st.session_state.analysis_data = analysis_data
                display_results(analysis_data, texts, lang)
            except Exception as e:
                st.error(f"{texts['error']}: {str(e)}")

    elif st.session_state.analysis_data:
        display_results(st.session_state.analysis_data, texts, lang)

if __name__ == "__main__":
    main()
