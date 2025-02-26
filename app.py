import streamlit as st
import requests
import json
import base64
import os
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

# Translations
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
        "error": "Error al procesar la solicitud. Intenta de nuevo.",
        "demo_header": "Demo",
        "demo_description": "Haz clic abajo para ejecutar un análisis con datos de muestra.",
        "demo_btn": "Ejecutar Análisis de Demostración",
        "demo_error": "Archivo de muestra no encontrado. Asegúrate de que 'sample_data.csv' esté en el repositorio."
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
        "error": "Error processing request. Please try again.",
        "demo_header": "Demo",
        "demo_description": "Click below to run an analysis with sample data.",
        "demo_btn": "Run Demo Analysis",
        "demo_error": "Sample file not found. Ensure 'sample_data.csv' is in the repository."
    },
    "pt": {
        "title": "BioChem Assistant - Analisador de Relatórios Bioquímicos com IA",
        "upload": "Carregar Dados",
        "analysis_type": "Tipo de Análise",
        "notes": "Notas Adicionais",
        "analyze": "Analisar Dados",
        "results": "Resultados da Análise",
        "new_analysis": "Nova Análise",
        "no_analysis": "Ainda sem análise",
        "no_analysis_desc": "Carregue seus dados bioquímicos para obter resultados detalhados.",
        "query": "Consulta Interativa",
        "query_placeholder": "Ex: O que significa um nível elevado de glicose?",
        "query_btn": "Consultar",
        "error": "Erro ao processar a solicitação. Tente novamente.",
        "demo_header": "Demo",
        "demo_description": "Clique abaixo para executar uma análise com dados de amostra.",
        "demo_btn": "Executar Análise de Demonstração",
        "demo_error": "Arquivo de amostra não encontrado. Certifique-se de que 'sample_data.csv' está no repositório."
    },
    "fr": {
        "title": "BioChem Assistant - Analyseur de Rapports Biochimiques avec IA",
        "upload": "Télécharger des Données",
        "analysis_type": "Type d'Analyse",
        "notes": "Notes Supplémentaires",
        "analyze": "Analyser les Données",
        "results": "Résultats de l'Analyse",
        "new_analysis": "Nouvelle Analyse",
        "no_analysis": "Pas encore d'analyse",
        "no_analysis_desc": "Téléchargez vos données biochimiques pour obtenir des résultats détaillés.",
        "query": "Requête Interactive",
        "query_placeholder": "Ex: Que signifie un niveau élevé de glucose ?",
        "query_btn": "Interroger",
        "error": "Erreur lors du traitement de la requête. Réessayez.",
        "demo_header": "Démo",
        "demo_description": "Cliquez ci-dessous pour exécuter une analyse avec des données d'exemple.",
        "demo_btn": "Exécuter l'Analyse de Démonstration",
        "demo_error": "Fichier d'exemple non trouvé. Assurez-vous que 'sample_data.csv' est dans le répertoire."
    }
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
    uploaded_files = st.sidebar.file_uploader("Archivos / Files", type=["csv", "txt", "pdf", "jpg", "jpeg", "png", "xlsx"], accept_multiple_files=True)
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files

    analysis_type = st.sidebar.selectbox(texts["analysis_type"], ["General", "Blood", "Genetic", "Cell", "Proteins"], index=0)
    notes = st.sidebar.text_area(texts["notes"], placeholder=texts["query_placeholder"].replace("Ej: ", "").replace("E.g.: ", "").replace("Ex: ", ""))

    analyze_btn = st.sidebar.button(texts["analyze"], disabled=not st.session_state.uploaded_files)

    # Demo section
    st.sidebar.header(texts["demo_header"])
    st.sidebar.write(texts["demo_description"])
    demo_btn = st.sidebar.button(texts["demo_btn"])

    # Main content
    if demo_btn:
        with st.spinner("Analizando datos de demostración... / Analyzing demo data..."):
            try:
                sample_file = "sample_data.csv"
                if not os.path.exists(sample_file):
                    st.error(texts["demo_error"])
                    return
                analysis_data = analyze_files([sample_file], analysis_type, notes, lang)
                st.session_state.analysis_data = analysis_data
                display_results(analysis_data, texts, lang)
            except Exception as e:
                st.error(f"{texts['error']}: {str(e)}")

    elif analyze_btn and st.session_state.uploaded_files:
        with st.spinner("Analizando datos... / Analyzing data..."):
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
    file_info = []
    for file in files:
        if isinstance(file, str):  # Demo file path
            with open(file, "rb") as f:
                content = f.read()
            name = os.path.basename(file)
            file_type = "text/csv"
        else:  # Uploaded file
            content = file.read()
            name = file.name
            file_type = file.type

        if file_type.startswith("image"):
            content = base64.b64encode(content).decode("utf-8")[:1000]
        else:
            content = content.decode("utf-8", errors="ignore")[:1000]
        file_info.append({"name": name, "type": file_type, "size": len(content), "content": content})

    prompt = f"""Analyze these biochemical files: {json.dumps(file_info)}. 
    Analysis type: {analysis_type.lower()}. Notes: {notes}. Respond in {lang}.
    Return a JSON with:
    - "summary": "2-3 sentence overview",
    - "findings": [{"title": "", "description": "", "severity": "normal|warning|critical"}, ...] (4 items),
    - "chartData": {"labels": ["Sample 1", ...], "datasets": [{"label": "hemoglobin", "data": [], "color": "#4c72b0"}, ...]},
    - "anomalies": ["", ...],
    - "recommendations": ["", ...].
    Use realistic medical ranges and terminology."""

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
    return json.loads(response.text)

def display_results(data, texts, lang):
    st.header(texts["results"])

    # Summary
    st.subheader("Resumen" if lang == "es" else "Résumé" if lang == "fr" else "Resumo" if lang == "pt" else "Summary")
    st.write(data["summary"])

    # Chart
    st.subheader("Visualización de Datos" if lang == "es" else "Visualisation des Données" if lang == "fr" else "Visualização de Dados" if lang == "pt" else "Data Visualization")
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
    st.subheader("Hallazgos Detallados" if lang == "es" else "Résultats Détaillés" if lang == "fr" else "Descobertas Detalhadas" if lang == "pt" else "Detailed Findings")
    for finding in data["findings"]:
        severity_color = {"normal": "blue", "warning": "orange", "critical": "red"}
        st.markdown(f"**{finding['title']}** (*{finding['severity']}*)", unsafe_allow_html=True)
        st.write(finding["description"])

    # Anomalies and Recommendations
    if data["anomalies"]:
        st.subheader("Anomalías" if lang == "es" else "Anomalies" if lang == "fr" else "Anomalias" if lang == "pt" else "Anomalies")
        st.write(", ".join(data["anomalies"]))
    if data["recommendations"]:
        st.subheader("Recomendaciones" if lang == "es" else "Recommandations" if lang == "fr" else "Recomendações" if lang == "pt" else "Recommendations")
        st.write(", ".join(data["recommendations"]))

    # Interactive Query
    st.subheader(texts["query"])
    query = st.text_input("Pregunta" if lang == "es" else "Question" if lang == "fr" else "Pergunta" if lang == "pt" else "Question", placeholder=texts["query_placeholder"])
    if st.button(texts["query_btn"]) and query:
        with st.spinner("Procesando... / Processing..."):
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
