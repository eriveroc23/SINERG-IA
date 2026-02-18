import os
import streamlit as st
from config import CONTRATOS_PATH, CHROMA_DB_PATH


def run_system_check():
    st.sidebar.markdown("### 🛠️ Diagnóstico del Sistema")

    checks = {
        "Carpeta de contratos": os.path.exists(CONTRATOS_PATH),
        "Base de datos Chroma": os.path.exists(CHROMA_DB_PATH),
        "API Key configurada": "GOOGLE_API_KEY" in os.environ or st.secrets.get("GOOGLE_API_KEY") is not None
    }



    # Verificar si hay PDFs en la carpeta
    if checks["Carpeta de contratos"]:
        pdfs = [f for f in os.listdir(CONTRATOS_PATH) if f.lower().endswith('.pdf')]
        checks["PDFs encontrados"] = len(pdfs) > 0
    else:
        checks["PDFs encontrados"] = False

    # Mostrar resultados en la barra lateral
    for label, status in checks.items():
        if status:
            st.sidebar.write(f"✅ {label}")
        else:
            st.sidebar.write(f"❌ {label}")
            if label == "Carpeta de contratos":
                st.sidebar.warning(f"Crea la carpeta en: {CONTRATOS_PATH}")
            if label == "PDFs encontrados":
                st.sidebar.warning("Añade archivos PDF a la carpeta 'contratos'.")

    return all(checks.values())

#Uso en la App:
if run_system_check():
    st.success("Sistema listo para operar")
else:
    st.error("El sistema requiere atención en los puntos marcados con ❌")