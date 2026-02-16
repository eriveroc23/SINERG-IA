# from langchain_community.vectorstores import Chroma
import logging
from datetime import datetime
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
#from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_classic.retrievers import EnsembleRetriever
from config import EMBEDDING_MODEL

import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import *
from prompts import *

@st.cache_resource
def initialize_rag_system():
    """
    Inicializa los componentes del sistema RAG:
    - Vector store (Chroma)
    - Modelos LLM para consultas y generación
    - Retriever con MMR y MultiQueryRetriever
    - Prompt base para RAG
    """
    # Vector Store
    vector_store = Chroma(
        embedding_function=GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL),
        persist_directory=CHROMA_DB_PATH,
    )

    # Modelos
    llm_queries = ChatGoogleGenerativeAI(
        model=QUERY_MODEL,
        temperature=0,
        max_retries=10,  # Aumenta los reintentos
        timeout=60,  # Espera más tiempo
    )
    llm_generation = ChatGoogleGenerativeAI(model=GENERATION_MODEL, temperature=0)

    # Retriever MMR (Maximum Marginal Relevance)
    base_retriever = vector_store.as_retriever(
        search_type=SEARCH_TYPE,
        search_kwargs={
            "k": SEARCH_K,
            "lambda_mult": MMR_DIVERSITY_LAMBDA,
            "fetch_k": MMR_FETCH_K,
        }
    )

    # Retriever adicional con similarity para comparar
    similarity_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": SEARCH_K}
    )

    # Prompt personalizado para MultiQueryRetriever
    multi_query_prompt = PromptTemplate.from_template(MULTI_QUERY_PROMPT)

    # MultiQueryRetriever con prompt personalizado
    mmr_multi_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm_queries,
        prompt=multi_query_prompt,
    )

    # Ensemble Retriever que combinar MMR y similarity
    if ENABLE_HYBRID_SEARCH:
        ensemble_retriever = EnsembleRetriever(
            retrievers=[mmr_multi_retriever, similarity_retriever],
            weights=[0.7, 0.3],  # mayor peso a MMR
            similarity_threshold=SIMILARITY_THRESHOLD
        )
        final_retriever = ensemble_retriever
    else:
        final_retriever = mmr_multi_retriever

    prompt = PromptTemplate.from_template(RAG_TEMPLATE)

    # Función para formatear y pre procesar los documentos recuperados
    def format_docs(docs):
        formatted = []

        for i, doc in enumerate(docs, 1):
            header = f"[Fragmento {i}]"

            if doc.metadata:
                if 'source' in doc.metadata:
                    source = doc.metadata['source'].split("\\")[-1] if '\\' in doc.metadata['source'] else doc.metadata[
                        'source']
                    header += f" - Fuente: {source}"
                if 'page' in doc.metadata:
                    header += f" - Pagina: {doc.metadata['page']}"

            content = doc.page_content.strip()
            formatted.append(f"{header}\n{content}")

        return "\n\n".join(formatted)

    rag_chain = (
            {
                "context": final_retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm_generation
            | StrOutputParser()
    )

    return rag_chain, mmr_multi_retriever

# Configuración básica de logging para ver en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ⚖️ [SISTEMA RAG] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- CONFIGURACIÓN PROFESIONAL DE LOGGING ---
def setup_logger():
    # Crear carpeta de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger_sys = logging.getLogger("SISTEMA_RAG")
    logger_sys.setLevel(logging.INFO)

    # Evitar duplicados si el logger ya existe
    if not logger_sys.handlers:
        # 1. Formato del mensaje: Fecha - Nivel - Mensaje
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')

        # 2. Handler para la TERMINAL
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger_sys.addHandler(console_handler)

        # 3. Handler para el ARCHIVO FÍSICO (Modo 'a' para anexar sin borrar lo previo)
        file_handler = logging.FileHandler('logs/historial_db.log', mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger_sys.addHandler(file_handler)

    return logger_sys





def ingest_docs():
    inicio = datetime.now()
    logger.info(">>> INICIO DE ACTUALIZACIÓN DE BDs <<<")

    try:
        # Carga de documentos
        loader = PyPDFDirectoryLoader(CONTRATOS_PATH)
        documentos = loader.load()
        logger.info(f"Archivos leídos: {len(documentos)} páginas cargadas.")

        # Fragmentación
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
        docs_split = text_splitter.split_documents(documentos)
        logger.info(f"Procesamiento: {len(docs_split)} fragmentos generados.")

        # Embeddings e Ingesta
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
        vector_store = Chroma.from_documents(
            documents=docs_split,
            embedding=embeddings,
            persist_directory=CHROMA_DB_PATH
        )

        tiempo_total = datetime.now() - inicio
        logger.info(f"--- ÉXITO: Base de datos actualizada en {tiempo_total.total_seconds():.2f}s ---")
        return vector_store

    except Exception as e:
        logger.error(f"!!! ERROR EN LA INGESTA: {str(e)}")
        raise e
def query_rag(question):
    try:
        rag_chain, retriever = initialize_rag_system()

        # Obtener respuesta
        response = rag_chain.invoke(question)

        # Obtener documentos para mostrarlos
        docs = retriever.invoke(question)

        # Formatear los documentos para mostrar
        docs_info = []
        for i, doc in enumerate(docs[:SEARCH_K], 1):
            doc_info = {
                "fragmento": i,
                "contenido": doc.page_content[:1000] + "..." if len(doc.page_content) > 1000 else doc.page_content,
                "fuente": doc.metadata.get('source', 'No especificada').split("\\")[-1],
                "pagina": doc.metadata.get('page', 'No especificada')
            }
            docs_info.append(doc_info)

        return response, docs_info

    except Exception as e:
        error_msg = f"Error al procesar la consulta: {str(e)}"
        return error_msg, []

def get_retriever_info():
    """Obtiene información sobre la configuración del retriever"""
    return {
        "tipo": f"{SEARCH_TYPE.upper()} + MultiQuery" + (" + Hybrid" if ENABLE_HYBRID_SEARCH else ""),
        "documentos": SEARCH_K,
        "diversidad": MMR_DIVERSITY_LAMBDA,
        "candidatos": MMR_FETCH_K,
        "umbral": SIMILARITY_THRESHOLD if ENABLE_HYBRID_SEARCH else "N/A"
    }