import os
import re
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- Configuración ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("✅ Modelo de Google AI configurado correctamente.")
except Exception as e:
    print(f"❌ Error al configurar Google AI: {e}")
    model = None

# --- Función de Limpieza (ya la teníamos, es útil) ---
def limpiar_markdown_links(texto):
    patron = r'\[([^\]]+)\]\(([^)]+)\)'
    def reemplazo(match):
        texto_visible, url = match.group(1), match.group(2)
        return url if texto_visible == url else f"{texto_visible} ({url})"
    return re.sub(patron, reemplazo, texto)

# --- Ruta del Webhook ---
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    if VERIFY_TOKEN and request.headers.get('Authorization') != VERIFY_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    user_message = data.get('query', {}).get('message')
    
    if not user_message:
        return jsonify({'error': 'No se encontró el mensaje.'}), 400

    print(f"🤖 Mensaje recibido: '{user_message}'")
    
    ai_response_raw = get_ai_response(user_message)
    ai_response_cleaned = limpiar_markdown_links(ai_response_raw)
    
    print(f"🧼 Respuesta limpia enviada: '{ai_response_cleaned}'")

    # --- LÍNEA CRÍTICA MODIFICADA SEGÚN LA DOCUMENTACIÓN ---
    # Creamos el formato de respuesta exacto que AutoResponder requiere.
    respuesta_json = {
        "replies": [
            {"message": ai_response_cleaned}
        ]
    }
    
    return jsonify(respuesta_json)

def get_ai_response(message):
    if not model:
        return "El modelo de IA no está disponible."
    try:
        prompt = f"Eres un asistente virtual para el servidor EXILIO. La web es https://exilio.muargentina.com. Responde a la siguiente consulta: '{message}'"
        response = model.generate_content(prompt)
        print(f"🧠 Respuesta cruda de la IA: '{response.text}'")
        return response.text
    except Exception as e:
        print(f"❌ Error en la llamada a Google Gemini: {e}")
        return "Lo siento, estoy teniendo un problema técnico para pensar mi respuesta."

@app.route('/')
def index():
    return "El cerebro del bot está en línea y configurado según la documentación oficial."