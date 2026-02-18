# pip install chromadb
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import *

def base_datos():

    loader = PyPDFDirectoryLoader("C:\\Users\\eduar\\PycharmProjects\\asistente_legal_RAG\\contratos")
    documentos = loader.load()

    print(f"Se cargaron {len(documentos)} paginas desde el directorio: {loader.path}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=1000
    )

    docs_split = text_splitter.split_documents(documentos)

    print(f"Se crearon {len(docs_split)} chunks de texto.")

    vector_stores = Chroma.from_documents(
        docs_split,
        embedding=GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL),
        persist_directory=CHROMA_DB_PATH
    )

    consulta = "¿Cual es la Documentación mínima a presentar?"

    resultado = vector_stores.similarity_search(consulta, k=3)

    print("Top 3 documentos más similares a la consulta:\n")
    for i, doc in enumerate(resultado, start=1):
        print(f"Contenido {doc.page_content}")
        print(f"Metadatos {doc.metadata}")


    return vector_stores