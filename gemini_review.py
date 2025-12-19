from google import genai
import os

# 1. Configuración
os.environ["GOOGLE_API_KEY"] = "AIzaSyBXlbw1LkrNTSIHr0urCFBpTnhe39UJG-Q"
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

print("Listado de modelos disponibles para tu cuenta:")
print("-" * 60)

# 2. Listar modelos
# En la nueva SDK, el atributo es 'supported_methods'
for model in client.models.list():
    if 'generateContent' in model.supported_actions:
        print(f"ID del modelo: {model.name} --> {model.input_token_limit}")