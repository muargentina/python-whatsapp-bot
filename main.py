import os
import re
import base64
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google.cloud import firestore
from google.oauth2 import service_account

load_dotenv()
app = Flask(__name__)

# --- Configuración de Claves ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# --- Configuración de la Base de Datos Firestore ---
try:
    # Decodificar las credenciales desde la variable de entorno Base64
    creds_b64 = os.getenv('FIRESTORE_CREDS_B64')
    creds_json_str = base64.b64decode(creds_b64).decode('utf-8')
    creds_json = json.loads(creds_json_str)
    credentials = service_account.Credentials.from_service_account_info(creds_json)
    db = firestore.Client(credentials=credentials)
    print("✅ Conexión a Firestore establecida correctamente.")
except Exception as e:
    print(f"❌ Error crítico al conectar con Firestore: {e}")
    db = None

# --- Configuración del Modelo de IA ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    # Mantenemos el modelo que elegiste
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ Modelo de Google AI configurado correctamente.")
except Exception as e:
    print(f"❌ Error al configurar Google AI: {e}")
    model = None

# --- Función de Limpieza (útil para los enlaces) ---
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
    query_data = data.get('query', {})
    user_message = query_data.get('message')
    sender_id = query_data.get('sender')
    
    if not user_message or not sender_id:
        return jsonify({'error': 'Faltan los campos "message" o "sender".'}), 400

    print(f"🤖 Mensaje recibido de '{sender_id}': '{user_message}'")
    
    ai_response_raw = get_ai_response(user_message, sender_id)
    ai_response_cleaned = limpiar_markdown_links(ai_response_raw)
    
    print(f"🧼 Respuesta limpia enviada a '{sender_id}': '{ai_response_cleaned}'")

    respuesta_json = {"replies": [{"message": ai_response_cleaned}]}
    return jsonify(respuesta_json)

# --- Función de IA (Reescrita con Corrección para Firestore) ---
def get_ai_response(message, sender_id):
    """Gestiona la conversación con memoria persistente en Firestore."""
    if not model or not db:
        return "El modelo de IA o la base de datos no están disponibles."

    doc_ref = db.collection('chat_histories').document(sender_id)
    doc = doc_ref.get()
    
    history = doc.to_dict().get('history', []) if doc.exists else []

    # Si el historial está vacío, es un usuario nuevo. Le damos la personalidad.
    if not history:
        print(f"💬 Creando nueva sesión de chat en Firestore para {sender_id}")
        initial_prompt_context = """
        **1. PERSONA:**
    Eres Atlas, el asistente virtual experto del servidor de juegos MU ARGENTINA , basado en el juego Online MU Online Season 6 Episodio 3. Tu tono es amigable, servicial y un poco entusiasta por el juego. Usas emojis pero no excesivamente.
    Si te piden cosas que solo el Staff de MU ARGENTINA puede resolver, di que envien un mensaje con la palabra STAFF , solamente la pabra STAFF sin mas y que aguarden que a la brevedad será atendido. 

    **2. CONTEXTO Y REGLAS:**
    Los links oficiales del juego son: https://muargentina.com Server EXILIO: https://exilio.muargentina.com y Server NORMAL: https://normal.muargentina.com nuestro Foro: https://foro.muargentina.com
    Las caracteristicas del servidor normal son: 
    El servidor NORMAL inicio desde 0 en Febrero de 2024
    Versión: SEASON 6 EP3
    Experiencia: x5/x7
    Drop: 40/45%
    Sistema de reset: Borra stat, recibis 200 puntos por reset
    Límite de resets: 40
    Tienda de items: NO (Solo consumibles ingame)

    Las caracteristicas del servidor EXILIO son: 
    El servidor EXILIO inicio desde 0 en Noviembre de 2022
    Versión: SEASON 6 EP3
    Experiencia: x500 (Dinamica)
    Drop: 50%
    Sistema de reset: No borra stat, quita el 2% del total de tus stat
    Límite de resets: Sin limite!
    Tienda de items: SI! en la web.

    En el server NORMAL puedes comprar WCoins desde la web, estos se utilizan para adquirir items que otros jugadores vendan en el Market de la web, o items consumibles en la tienda dentro del juego (Para ver esta tienda debes presionar la tecla X, dentro de la zona segura de una ciudad.
    Para comprar items en la tienda de EXILIO necesitas Creditos, se compran allí mismo en el panel de tu cuenta, inicia sesión y veras la opción.
    Por ahora los metodos de pago disponibles son MercadoPago y PayPal
    Se estan planeando abrir 2 servidores nuevos, uno en poco tiempo y otro cerca de fin de año.
    Si el juego carga pero no inicia, probablemente deban añadir el main.exe al DEP de Windows. Guia para añadir el main.exe al DEP de Windows, Presiona la tecla Windows, escribe "Mi equipo" , dale click derecho y presiona en Propiedades, luego busca a la derecha o izquierda de la pantalla donde diga Configuración avanzada del sistema y haz clic allí, luego ve a la pestaña opciones avanzadas, en la sección Rendimiento haz clic en configuración, Ve a la pestaña "Prevención de ejecución de datos" y activa la opción "Activar DEP para todos los programas y servicios excepto los que yo seleccione" , Haz clic en "Agregar" y busca la ubicación donde instalaste el juego, allí selecciona main.exe , luego presiona en Aplicar y Aceptar, Se recomienda reiniciar la computadora para que los cambios se apliquen correctamente.
    El reseteo o reinicio del árbol de habilidades skilltree no se encuentra habilitado momentáneamente pero se esta trabajando en buscar una solución para que los jugadores puedan usar esta función.
        """
        history = [
            {'role': 'user', 'parts': ["Hola, por favor asume la siguiente personalidad y contexto para nuestra conversación."]},
            {'role': 'model', 'parts': [initial_prompt_context]},
        ]

    chat = model.start_chat(history=history)
    
    try:
        response = chat.send_message(message)
        
        # --- LÍNEA CRÍTICA CORREGIDA ---
        # "Traducimos" manualmente el historial al formato JSON correcto antes de guardarlo.
        history_for_db = [{'role': part.role, 'parts': [p.text for p in part.parts]} for part in chat.history]
        doc_ref.set({'history': history_for_db})

        print(f"🧠 Respuesta generada para '{sender_id}': '{response.text}'")
        return response.text
    except Exception as e:
        print(f"❌ Error en la llamada a Google Gemini o BD: {e}")
        return "Lo siento, estoy teniendo un problema técnico para pensar mi respuesta."

# --- Ruta de prueba ---
@app.route('/')
def index():
    return "El cerebro del bot (con memoria en Firestore) está en línea."
