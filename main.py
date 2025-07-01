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
# --- Ruta del Webhook (VERSIÓN DE DIAGNÓSTICO) ---
@app.route('/webhook', methods=['GET', 'POST']) # Aceptamos GET y POST
def handle_webhook():
    print("--- INICIO DEPURACIÓN AVANZADA ---")
    print(f"Método HTTP recibido: {request.method}")
    print("--- Cabeceras (Headers) ---")
    print(request.headers)
    
    user_message = None
    
    if request.method == 'POST':
        # Intentamos obtener datos del cuerpo (body) si es POST
        data = request.get_json(silent=True) or {}
        print(f"Cuerpo (Body) JSON recibido: {data}")
        user_message = data.get('query')

    # También revisamos si los datos vienen en la URL (query parameters)
    # Esto es típico de un GET, pero a veces viene en POST también
    args = request.args
    print(f"Argumentos de la URL (Query Params) recibidos: {args}")
    if not user_message:
        user_message = args.get('query')

    print(f"Mensaje del usuario extraído: {user_message}")
    print("--- FIN DEPURACIÓN AVANZADA ---")

    if not user_message:
        # Si después de todo no encontramos el mensaje, devolvemos un error.
        return jsonify({'error': 'No se encontró el parámetro "query" en la petición.'}), 400

    # El resto del código sigue igual...
    ai_response = get_ai_response(user_message)
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