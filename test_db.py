import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import CHROMA_DB_PATH
from config import EMBEDDING_MODEL

def verify_chroma_db():
    print("--- 🔍 Iniciando Verificación de Chroma ---")

    # 1. Configurar Embeddings (debe ser el mismo que usaste al crear la DB)
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    # 2. Cargar la DB desde el directorio persistente
    # Asegúrate de que esta ruta coincida con la de tu config.py
    persist_directory = CHROMA_DB_PATH

    if not os.path.exists(persist_directory):
        print(f"❌ ERROR: No se encontró la carpeta {persist_directory}")
        return

    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )

    # 3. Verificar cantidad de documentos
    collection_count = vector_db._collection.count()
    print(f"✅ Conexión exitosa. Fragmentos totales en la DB: {collection_count}")

    if collection_count == 0:
        print("⚠️ La base de datos está vacía. Revisa el proceso de carga.")
        return

    # 4. Prueba de recuperación (Similitud Simple)
    test_query = "garaje"  # Cambia esto por una palabra clave de tus contratos
    print(f"\n--- 🧪 Probando búsqueda para: '{test_query}' ---")

    docs = vector_db.similarity_search(test_query, k=2)

    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get('source', 'Desconocida')
        page = doc.metadata.get('page', 'N/A')
        print(f"\n[Resultado {i}]")
        print(f"📄 Fuente: {source} (Pág. {page})")
        print(f"✂️ Contenido: {doc.page_content[:150]}...")


if __name__ == "__main__":
    verify_chroma_db()