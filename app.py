import streamlit as st


import config
from rag_system import query_rag, get_retriever_info, ingest_docs
import time
import os
import pandas as pd
from config import CONTRATOS_PATH

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema RAG - Asistente Legal",
    page_icon="⚖️",
    layout="wide"
)

# --- INICIALIZACIÓN DE ESTADOS ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploader_id" not in st.session_state:
    st.session_state.uploader_id = 0

if "show_success_toast" not in st.session_state:
    st.session_state.show_success_toast = False

# --- LÓGICA DE NOTIFICACIONES (TOAST) ---
if st.session_state.show_success_toast:
    try:
        num_contratos = len([f for f in os.listdir(CONTRATOS_PATH) if f.endswith('.pdf')])
        st.toast(f"✅ ¡Base de datos actualizada! {num_contratos} contratos listos.", icon="⚖️")
        st.session_state.show_success_toast = False
    except Exception:
        pass


# --- FUNCIONES DE APOYO ---
def save_uploaded_file(uploaded_file):
    if not os.path.exists(CONTRATOS_PATH):
        os.makedirs(CONTRATOS_PATH)
    file_path = os.path.join(CONTRATOS_PATH, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def obtener_info_archivos(ruta):
    archivos = []
    if os.path.exists(ruta):
        for nombre in os.listdir(ruta):
            if nombre.endswith(".pdf"):
                path_completo = os.path.join(ruta, nombre)
                stats = os.stat(path_completo)
                fecha_mod = time.strftime('%d/%m/%Y %H:%M', time.localtime(stats.st_mtime))
                tamano = f"{round(stats.st_size / (1024 * 1024), 2)} MB"
                archivos.append({
                    "Archivo": nombre,
                    "Fecha de Carga": fecha_mod,
                    "Tamaño": tamano
                })
    return archivos


# --- TÍTULO ---
st.title("⚖️ Sistema RAG - Asistente Legal")
st.divider()

# --- SIDEBAR: GESTIÓN DE DOCUMENTOS ---
with st.sidebar:
    st.header("📋 Gestión de Documentos")

    uploaded_files = st.file_uploader(
        "Añadir nuevos contratos (PDF)",
        type="pdf",
        accept_multiple_files=True,
        key=f"pdf_uploader_{st.session_state.uploader_id}"
    )

    # Actualización: width='stretch' reemplaza use_container_width=True
    if st.button("🚀 Procesar e Indexar", width='stretch'):
        if uploaded_files:
            with st.status("Sincronizando base de conocimientos...", expanded=True) as status:
                for uploaded_file in uploaded_files:
                    st.write(f"Guardando {uploaded_file.name}...")
                    save_uploaded_file(uploaded_file)

                st.write("Actualizando vectores en Chroma...")
                ingest_docs()

                st.cache_resource.clear()
                st.session_state.uploader_id += 1
                st.session_state.show_success_toast = True

                status.update(label="✅ Sincronización exitosa", state="complete")
            st.rerun()
        else:
            st.warning("Selecciona archivos primero.")

    st.divider()

    # Info del sistema
    with st.container(border=True):
        try:
            retriever_info = get_retriever_info()
            st.markdown(f"**🔍 Retriever:**")
            st.markdown(f"`{retriever_info['tipo']}`")
        except:
            st.caption("🔍 Retriever: No inicializado")

    # Tarjeta de Modelos
    with st.container(border=True):
        query_model = config.QUERY_MODEL
        response_model = config.GENERATION_MODEL
        st.markdown("🤖 **Modelos de IA**")
        st.markdown(f"**Consulta:** `{query_model}` \n\n**Respuesta:** `{response_model}`")

    # Actualización: width='stretch' reemplaza use_container_width=True
    if st.button("🗑️ Limpiar Chat", type="secondary", width='stretch'):
        st.session_state.messages = []
        st.rerun()

# --- LAYOUT PRINCIPAL ---
col1, col2 = st.columns([2, 1])

with col1:
    tab_chat, tab_historial = st.tabs(["💬 Chat de Consulta", "📜 Historial de Cargas"])

    with tab_chat:
        chat_container = st.container(height=500)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    with tab_historial:
        st.markdown("### 📜 Inventario de Documentos")
        lista_archivos = obtener_info_archivos(CONTRATOS_PATH)

        if lista_archivos:
            df_archivos = pd.DataFrame(lista_archivos)
            # Actualización: width='stretch' reemplaza use_container_width=True
            st.dataframe(df_archivos, width='stretch', hide_index=True)

            # Botón para descargar inventario
            csv = df_archivos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Inventario (CSV)",
                data=csv,
                file_name="inventario_contratos.csv",
                mime="text/csv",
            )
        else:
            st.info("No hay documentos indexados aún.")

with col2:
    st.markdown("### 📄 Documentos Relevantes")
    docs_to_show = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant" and "docs" in msg:
            docs_to_show = msg["docs"]
            break

    if docs_to_show:
        for doc in docs_to_show:
            with st.expander(f"📄 Fragmento {doc['fragmento']} - {doc['fuente']}", expanded=False):
                st.markdown(f"**Página:** {doc['pagina']}")
                st.caption(doc['contenido'])
    else:
        st.info("Los fragmentos del contrato aparecerán aquí al consultar.")

# --- PROCESAMIENTO DE CHAT ---
if prompt := st.chat_input("Consulta tus contratos..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_prompt = st.session_state.messages[-1]["content"]
    with col1:
        with st.chat_message("assistant"):
            with st.status("⚖️ Analizando documentos legales...", expanded=True) as status:
                st.write("🔍 Aplicando Multi-Query...")
                time.sleep(0.3)
                st.write("📂 Recuperando contexto relevante...")
                response, docs = query_rag(last_prompt)
                status.update(label="✅ Análisis finalizado", state="complete", expanded=False)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response, "docs": docs})
    st.rerun()

# --- FOOTER ---
st.divider()
st.markdown("<div style='text-align: center; color: #666;'>🏛️ Asistente Legal con Google Gemini & Chroma DB</div>",
            unsafe_allow_html=True)