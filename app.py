
import os
import streamlit as st

import config






try:
    from rag_system import query_rag, get_retriever_info, ingest_docs
    RAG_AVAILABLE = True
    RAG_IMPORT_ERROR = None
except Exception as _e:
    # Guardar el error para mostrar instrucciones en la UI
    RAG_AVAILABLE = False
    RAG_IMPORT_ERROR = _e

import time
import os
import pandas as pd
from config import CONTRATOS_PATH

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SINERG-IA",
    page_icon=":diamond_shape_with_a_dot_inside:",
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


def leer_logs_con_formato(ruta_log='logs/historial_db.log', n_lineas=20):
    if os.path.exists(ruta_log):
        with open(ruta_log, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            ultimas_lineas = lineas[-n_lineas:]

            # Procesamos cada línea para añadir indicadores visuales
            log_formateado = ""
            for linea in ultimas_lineas:
                if "[ERROR]" in linea:
                    log_formateado += f"❌ {linea}"
                elif "[WARNING]" in linea:
                    log_formateado += f"⚠️ {linea}"
                elif "ÉXITO" in linea or "EXITOSAMENTE" in linea:
                    log_formateado += f"✅ {linea}"
                else:
                    log_formateado += f"🔹 {linea}"
            return log_formateado
    return "No se encontraron registros de actividad."

# --- TÍTULO ---
st.title(":diamond_shape_with_a_dot_inside: SINERG-IA: El núcleo de inteligencia de Grupo FOA")
st.divider()

# --- SIDEBAR: GESTIÓN DE DOCUMENTOS ---
with st.sidebar:
    st.header("📋 Gestión de Documentos")

    uploaded_files = st.file_uploader(
        "Añadir nuevos documentos (PDF)",
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
                if RAG_AVAILABLE:
                    try:
                        ingest_docs()
                    except Exception as e:
                        st.error(f"Error al ejecutar ingest_docs: {e}")
                else:
                    st.error("El componente RAG no está disponible en este entorno. Revisa los logs y las dependencias (requirements).")
                    if RAG_IMPORT_ERROR:
                        st.caption(str(RAG_IMPORT_ERROR))

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
    # Añadimos la tercera pestaña "🖥️ Monitor"
    tab_chat, tab_historial, tab_monitor = st.tabs([
        "💬 Consultoría Inteligente",
        "📜 Archivo Documental",
        "🖥️ Monitor de Sistema"
    ])

    with tab_chat:
        # Contenedor principal con borde sutil para delimitar el área de trabajo
        with st.container(border=True):
            chat_container = st.container(height=550)

            with chat_container:
                if not st.session_state.messages:
                    # Estado vacío con diseño elegante
                    st.markdown(
                        """
                        <div style="text-align: center; padding: 50px; color: #888;">
                            <h3 style="margin-bottom: 10px;">💬 Bienvenido a SINERG-IA: El núcleo de inteligencia de Grupo FOA</h3>
                            <p>¿En qué puedo apoyarte hoy? Puedo ayudarte con:<br>
                                <br>📐 Consultas Técnicas: Especificaciones, planos y normativas.
                                <br>⚖️ Análisis Legal: Revisión de contratos y cumplimiento.
                                <br>💼 Gestión Administrativa: Trazabilidad de procesos y control documental.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        # Diseño de burbuja basado en el rol
                        if message["role"] == "user":
                            st.markdown(f"**Tú:** {message['content']}")
                        else:
                            # Respuesta del asistente con formato Markdown optimizado
                            st.markdown("##### SINERG-IA")
                            st.markdown(message["content"])

                            # Si hay documentos, mostrar un pequeño badge indicador
                            if "docs" in message and message["docs"]:
                                st.caption(f"📍 Basado en {len(message['docs'])} fuentes del archivo.")

    with tab_historial:
        # Aquí integramos el diseño de tabla que definimos anteriormente
        st.markdown("### 📜 Repositorio de Conocimiento")
        lista_archivos = obtener_info_archivos(CONTRATOS_PATH)

        if lista_archivos:
            # Estilo de tabla "Premium" usando dataframe con configuración de columna
            df_archivos = pd.DataFrame(lista_archivos)
            st.dataframe(
                df_archivos,
                width='stretch',
                hide_index=True,
                column_config={
                    "Archivo": st.column_config.TextColumn("Nombre del Documento", width="large"),
                    "Fecha de Carga": st.column_config.TextColumn("📅 Fecha"),
                    "Tamaño": st.column_config.TextColumn("📦 Tamaño")
                }
            )

            col_down, col_info = st.columns([1, 1])
            with col_down:
                csv = df_archivos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar Inventario",
                    data=csv,
                    file_name="inventario_legal.csv",
                    mime="text/csv",
                    width='stretch'
                )
        else:
            st.info("El archivo documental está vacío. Por favor, cargue documentos en la barra lateral.")

    with tab_monitor:
        st.markdown("### 🖥️ Consola de Diagnóstico")

        # Creamos un contenedor vacío para que el log se imprima siempre actualizado
        placeholder_log = st.empty()

        # Obtenemos los logs procesados
        logs_texto = leer_logs_con_formato()

        # Mostramos el log dentro del placeholder
        placeholder_log.text_area(
            label="Eventos recientes del motor RAG",
            value=logs_texto,
            height=400,
            key=f"log_area_{st.session_state.uploader_id}",  # Clave dinámica para forzar renderizado
            help="Los errores críticos aparecen marcados con ❌"
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            # El botón ahora limpia el estado previo antes de reiniciar
            if st.button("🔄 Refrescar Consola", width='stretch'):
                # Pequeño truco: actualizamos el ID para que Streamlit
                # regenere el widget de texto por completo
                st.session_state.uploader_id += 1
                st.rerun()
        with col_btn2:
            if os.path.exists('logs/historial_db.log'):
                with open('logs/historial_db.log', 'rb') as f:
                    st.download_button(
                        label="📥 Descargar Log Completo",
                        data=f,
                        file_name="historial_tecnico.log",
                        mime="text/plain",
                        width='stretch'
                    )

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
        st.info("Los fragmentos del documento aparecerán aquí al consultar.")

# --- PROCESAMIENTO DE CHAT ---
if prompt := st.chat_input("Realiza una consulta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_prompt = st.session_state.messages[-1]["content"]
    with col1:
        with st.chat_message("assistant"):
            with st.status("🧠 Analizando la base de conocimiento de SINERG-IA...", expanded=True) as status:
                st.write("🔍 Aplicando Multi-Query...")
                time.sleep(0.3)
                st.write("📂 Recuperando contexto relevante...")
                if RAG_AVAILABLE:
                    try:
                        response, docs = query_rag(last_prompt)
                    except Exception as e:
                        response = "El motor RAG falló al procesar la consulta. Revisa los logs."
                        docs = []
                        st.error(f"Error interno: {e}")
                else:
                    response = "El motor RAG no está disponible en este despliegue. Revisa las dependencias y el archivo requirements."
                    docs = []
                    if RAG_IMPORT_ERROR:
                        st.caption(str(RAG_IMPORT_ERROR))
                status.update(label="✅ Análisis finalizado", state="complete", expanded=False)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response, "docs": docs})
    st.rerun()

# --- FOOTER ---
st.divider()
st.markdown("<div style='text-align: center; color: #666;'>Desarrollado con Google Gemini & Chroma DB</div>",
            unsafe_allow_html=True)