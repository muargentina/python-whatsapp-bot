import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

app = Flask(__name__)

# --- Configuración de Claves y Modelos ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN") # Opcional, para seguridad

# Configurar el modelo de IA de Google Gemini
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Modelo de Google AI configurado correctamente.")
except Exception as e:
    print(f"❌ Error al configurar Google AI: {e}")
    model = None

# --- Ruta del Webhook (VERSIÓN DE PRUEBA CON RESPUESTA FIJA) ---
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # La verificación de seguridad sigue igual
    if VERIFY_TOKEN and request.headers.get('Authorization') != VERIFY_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 403

    # Recibimos el mensaje pero lo ignoramos por ahora
    data = request.get_json()
    query_data = data.get('query', {})
    user_message = query_data.get('message')
    print(f"🤖 Mensaje recibido: '{user_message}' (será ignorado por la prueba)")

    # ¡PASO CLAVE! En lugar de llamar a la IA, definimos una respuesta simple y fija.
    respuesta_fija = "Esta es una respuesta de prueba."
    
    print(f"🧼 Enviando respuesta fija: '{respuesta_fija}'")

    # Enviamos la respuesta fija en el formato que AutoResponder espera
    return jsonify({'replies': [respuesta_fija]})

def get_ai_response(message):
    """Llama a Google Gemini para obtener una respuesta inteligente."""
    if not model:
        return "El modelo de IA no está disponible."
    try:
        # Aquí puedes mejorar el prompt para darle más contexto a la IA
        prompt = f"Eres un asistente virtual para mi negocio. Sé amable, conciso y profesional. Responde a la siguiente consulta: '{message}'"
        response = model.generate_content(prompt)
        print(f"🧠 Respuesta generada: '{response.text}'")
        return response.text
    except Exception as e:
        print(f"❌ Error en la llamada a Google Gemini: {e}")
        return "Lo siento, estoy teniendo un problema técnico para pensar mi respuesta."

# --- Ruta de prueba ---
@app.route('/')
def index():
    return "El cerebro del bot está en línea."