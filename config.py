import os

# ls -l .\chroma.sqlite3

# Obtener la ruta del directorio actual donde está este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas Relativas (Evitan conflictos de permisos en Windows)
CONTRATOS_PATH = os.path.join(BASE_DIR, "contratos")
# CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# Configuración de modelos GOOGLE
EMBEDDING_MODEL = "gemini-embedding-001"
#EMBEDDING_MODEL = "models/embedding-001"
QUERY_MODEL = "gemini-flash-latest"
GENERATION_MODEL = "gemini-flash-latest"

# # Configuración de modelos OPENAI
# EMBEDDING_MODEL = "text-embedding-3-large"
# QUERY_MODEL = "gpt-4o-mini"
# GENERATION_MODEL = "gpt-4o"

# Configuración del vector store
CHROMA_DB_PATH = "/workspaces/SINERG-IA/"

# Configuración del retriever
SEARCH_TYPE = "mmr"
MMR_DIVERSITY_LAMBDA = 0.7
MMR_FETCH_K = 20
SEARCH_K = 4

# Configuración alternativa para retriever híbrido
ENABLE_HYBRID_SEARCH = True
SIMILARITY_THRESHOLD = 0.70