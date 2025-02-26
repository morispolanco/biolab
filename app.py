import streamlit as st
import requests
import json
import base64
from io import BytesIO
import plotly.graph_objects as go

# API Configuration
API_KEY = "AIzaSyBYB7NK1nkDg7Y2tno6aU8bWbWFMK65LYo"  # Replace with st.secrets["API_KEY"] for security
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Supported languages
LANGUAGES = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
    "fr": "Français"
}

# Translations (simplified; expand as needed)
TRANSLATIONS = {
    "es": {
        "title": "BioChem Assistant - Analizador de Informes Bioquímicos con IA",
        "upload": "Subir Datos",
        "analysis_type": "Tipo de Análisis",
        "notes": "Notas Adicionales",
        "analyze": "Analizar Datos",
        "results": "Resultados del Análisis",
        "new_analysis": "Nuevo Análisis",
        "no_analysis": "Aún no hay análisis",
        "no_analysis_desc": "Sube tus datos bioquímicos para obtener resultados detallados.",
        "query": "Consulta Interactiva",
        "query_placeholder": "Ej: ¿Qué significa un nivel elevado de glucosa?",
        "query_btn": "Consultar",
        "error": "Error al procesar la solicitud. Intenta de nuevo."
    },
    "en": {
        "title": "BioChem Assistant - Biochemical Reports Analyzer with AI",
        "upload": "Upload Data",
        "analysis_type": "Analysis Type",
        "notes": "Additional Notes",
        "analyze": "Analyze Data",
        "results": "Analysis Results",
        "new_analysis": "New Analysis",
        "no_analysis": "No analysis yet",
        "no_analysis_desc": "Upload your biochemical data to get detailed results.",
        "query": "Interactive Query",
        "query_placeholder": "E.g.: What does an elevated glucose level mean?",
        "query_btn": "Query",
        "error": "Error processing request. Please try again."
    }
    # Add "pt" and "fr" translations if needed
}

# Session state
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Main app
def main():
    # Language selection
    lang = st.sidebar.selectbox("Idioma / Language", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], index=0)
    texts = TRANSLATIONS.get(lang, TRANSLATIONS["es"])

    # Title
    st.title(texts["title"])

    # Sidebar inputs
    st.sidebar.header(texts["upload"])
    uploaded_files = st.sidebar.file_uploader("Archivos", type=["csv", "txt", "pdf", "jpg", "jpeg", "png", "xlsx"], accept_multiple_files=True)
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files

    analysis_type = st.sidebar.selectbox(texts["analysis_type"], ["General", "Blood", "Genetic", "Cell", "Proteins"], index=0)
    notes = st.sidebar.text_area(texts["notes"], placeholder=texts["query_placeholder"].replace("Ej: ", "").replace("E.g.: ", ""))

    analyze_btn = st.sidebar.button(texts["analyze"], disabled=not st.session_state.uploaded_files)

    # Main content
    if analyze_btn and st.session_state.uploaded_files:
        with st.spinner("Analizando datos..."):
            try:
                analysis_data = analyze_files(st.session_state.uploaded_files, analysis_type, notes, lang)
                st.session_state.analysis_data = analysis_data
                display_results(analysis_data, texts, lang)
            except Exception as e:
                st.error(f"{texts['error']}: {str(e)}")

    elif st.session_state.analysis_data:
        display_results(st.session_state.analysis_data, texts, lang)
    else:
        st.info(f"{texts['no_analysis']}: {texts['no_analysis_desc']}")

    # New Analysis button
    if st.session_state.analysis_data and st.sidebar.button(texts["new_analysis"]):
        st.session_state.analysis_data = None
        st.session_state.uploaded_files = []
        st.rerun()

def analyze_files(files, analysis_type, notes, lang):
    # Process files
    file_info = []
    for file in files:
        if file.type.startswith("image"):
            content = base64.b64encode(file.read()).decode("utf-8")
            file_info.append({"name": file.name, "type": file.type, "size": file.size, "content": content[:1000]})
        else:
            content = file.read().decode("utf-8", errors="ignore")
            file_info.append({"name": file.name, "type": file.type, "size": file.size, "content": content[:1000]})

    # Construct prompt
    prompt = f"""Analyze these biochemical files: {json.dumps(file_info)}. 
    Analysis type: {analysis_type.lower()}. Notes: {notes}. Respond in {lang}.
    Return a JSON with:
    - "summary": "2-3 sentence overview",
    - "findings": [{"title": "", "description": "", "severity": "normal|warning|critical"}, ...] (4 items),
    - "chartData": {"labels": ["Sample 1", ...], "datasets": [{"label": "hemoglobin", "data": [], "color": "#4c72b0"}, ...]},
    - "anomalies": ["", ...],
    - "recommendations": ["", ...].
    Use realistic medical ranges and terminology."""

    # API payload matching curl
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 1,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "text/plain"
        }
    }

    # Make API request
    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=payload)
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")
    return json.loads(response.text)

def display_results(data, texts, lang):
    st.header(texts["results"])

    # Summary
    st.subheader("Resumen" if lang == "es" else "Summary")
    st.write(data["summary"])

    # Chart
    st.subheader("Visualización de Datos" if lang == "es" else "Data Visualization")
    fig = go.Figure()
    for dataset in data["chartData"]["datasets"]:
        fig.add_trace(go.Scatter(
            x=data["chartData"]["labels"],
            y=dataset["data"],
            mode="lines+markers",
            name=dataset["label"],
            line=dict(color=dataset["color"])
        ))
    st.plotly_chart(fig, use_container_width=True)

    # Detailed Findings
    st.subheader("Hallazgos Detallados" if lang == "es" else "Detailed Findings")
    for finding in data["findings"]:
        severity_color = {"normal": "blue", "warning": "orange", "critical": "red"}
        st.markdown(f"**{finding['title']}** (*{finding['severity']}*)", unsafe_allow_html=True)
        st.write(finding["description"])

    # Anomalies and Recommendations
    if data["anomalies"]:
        st.subheader("Anomalías" if lang == "es" else "Anomalies")
        st.write(", ".join(data["anomalies"]))
    if data["recommendations"]:
        st.subheader("Recomendaciones" if lang == "es" else "Recommendations")
        st.write(", ".join(data["recommendations"]))

    # Interactive Query
    st.subheader(texts["query"])
    query = st.text_input("Pregunta" if lang == "es" else "Question", placeholder=texts["query_placeholder"])
    if st.button(texts["query_btn"]) and query:
        with st.spinner("Procesando..."):
            try:
                response = query_data(query, data, lang)
                st.write(response)
            except Exception as e:
                st.error(f"{texts['error']}: {str(e)}")

def query_data(query, analysis_data, lang):
    context = f"Summary: {analysis_data['summary']}\nFindings: {json.dumps(analysis_data['findings'])}"
    prompt = f"You are BioChem Assistant. User's question: '{query}'. Context: {context}. Answer concisely in {lang}."

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 1,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "text/plain"
        }
    }

    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=payload)
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")
    return response.text

if __name__ == "__main__":
    main()
