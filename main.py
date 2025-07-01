import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# --- Configuración de Claves y Modelos ---
# Clave para la IA de Google (obligatoria)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Token para asegurar nuestro webhook (opcional pero recomendado)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# Configurar el modelo de IA de Google Gemini
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Modelo de Google AI configurado correctamente.")
except Exception as e:
    print(f"Error al configurar Google AI: {e}")
    model = None

# --- Ruta del Webhook ---
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # (Opcional) Verificación de seguridad
    if VERIFY_TOKEN:
        auth_header = request.headers.get('Authorization')
        if auth_header != VERIFY_TOKEN:
            print("Acceso denegado: Token de verificación inválido.")
            return jsonify({'error': 'Unauthorized'}), 403

    # Obtener el mensaje enviado por AutoResponder
    data = request.get_json()
    user_message = data.get('query') # AutoResponder suele usar el campo 'query'

    if not user_message:
        return jsonify({'error': 'No se recibió ningún mensaje (query).'}), 400

    print(f"Mensaje recibido de AutoResponder: '{user_message}'")
    
    # Obtener la respuesta de la IA
    ai_response = get_ai_response(user_message)
    
    # Devolver la respuesta en formato JSON para que AutoResponder la lea
    return jsonify({'reply': ai_response})

def get_ai_response(message):
    """Llama a Google Gemini para obtener una respuesta inteligente."""
    if not model:
        return "El modelo de IA no está disponible en este momento."
    try:
        # Aquí puedes mejorar el prompt para darle más contexto a la IA
        prompt = f"Eres un asistente virtual para mi negocio. Sé amable, conciso y profesional. Responde a la siguiente consulta de un cliente: '{message}'"
        response = model.generate_content(prompt)
        print(f"Respuesta generada por la IA: '{response.text}'")
        return response.text
    except Exception as e:
        print(f"Error en la llamada a la API de Google Gemini: {e}")
        return "Lo siento, estoy teniendo un problema técnico para pensar mi respuesta."

# --- Ruta de prueba para verificar que el servidor está vivo ---
@app.route('/')
def index():
    return "El cerebro de tu bot está en línea. ¡Listo para recibir conexiones desde AutoResponder!"

if __name__ == '__main__':
    # Gunicorn usará el objeto 'app', no necesitamos app.run() para producción
    pass