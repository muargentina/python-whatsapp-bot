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

# Diccionario para guardar las conversaciones en memoria
# La clave será el número de teléfono del usuario, el valor será la sesión de chat.
conversations = {}

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ Modelo de Google AI configurado correctamente.")
except Exception as e:
    print(f"❌ Error al configurar Google AI: {e}")
    model = None

# --- Función de Limpieza (la mantenemos) ---
def limpiar_markdown_links(texto):
    patron = r'\[([^\]]+)\]\(([^)]+)\)'
    def reemplazo(match):
        texto_visible, url = match.group(1), match.group(2)
        return url if texto_visible == url else f"{texto_visible} ({url})"
    return re.sub(patron, reemplazo, texto)

# --- Ruta del Webhook (Modificada) ---
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    if VERIFY_TOKEN and request.headers.get('Authorization') != VERIFY_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    query_data = data.get('query', {})
    user_message = query_data.get('message')
    # ¡NUEVO! Obtenemos el ID del remitente para identificar la conversación
    sender_id = query_data.get('sender')
    
    if not user_message or not sender_id:
        return jsonify({'error': 'Faltan los campos "message" o "sender".'}), 400

    print(f"🤖 Mensaje recibido de '{sender_id}': '{user_message}'")
    
    # Pasamos el sender_id a la función de la IA para que use la memoria
    ai_response_raw = get_ai_response(user_message, sender_id)
    ai_response_cleaned = limpiar_markdown_links(ai_response_raw)
    
    print(f"🧼 Respuesta limpia enviada a '{sender_id}': '{ai_response_cleaned}'")

    respuesta_json = {"replies": [{"message": ai_response_cleaned}]}
    return jsonify(respuesta_json)

# --- Función de IA (Reescrita con Memoria) ---
def get_ai_response(message, sender_id):
    """Gestiona la conversación con memoria para cada usuario."""
    if not model:
        return "El modelo de IA no está disponible."

    # Revisa si ya tenemos una conversación con este usuario
    if sender_id not in conversations:
        # Si no, crea una nueva sesión de chat con el historial inicial (la personalidad)
        print(f"💬 Creando nueva sesión de chat para {sender_id}")
        
        # El prompt inicial ahora se convierte en el primer mensaje de la historia
        initial_prompt_context = """
    **1. PERSONA:**
    Eres Atlas, el asistente virtual experto del servidor de juegos MU ARGENTINA , basado en el juego Online MU Online Season 6 Episodio 3. Tu tono es amigable, servicial y un poco entusiasta por el juego. Usas emojis pero no excesivamente.
    Si te piden cosas que solo el Staff de MU ARGENTINA puede resolver, di que aguarden en el chat hasta que algun administrador pueda leerlo, y no respondas hasta que en el chat se vuelva a enviar la palabra ATLAS , mientras tanto no respondas a los mensajes que se envien ignoralos. 

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
        
        # Creamos el historial de chat con el contexto
        conversations[sender_id] = model.start_chat(history=[
            {'role': 'user', 'parts': ["Hola, por favor asume la siguiente personalidad y contexto para nuestra conversación."]},
            {'role': 'model', 'parts': [initial_prompt_context]},
        ])
    
    chat = conversations[sender_id]
    
    try:
        # Enviamos el nuevo mensaje dentro de la sesión de chat existente
        response = chat.send_message(message)
        print(f"🧠 Respuesta generada para '{sender_id}': '{response.text}'")
        return response.text
    except Exception as e:
        print(f"❌ Error en la llamada a Google Gemini: {e}")
        return "Lo siento, estoy teniendo un problema técnico para pensar mi respuesta."

@app.route('/')
def index():
    return "El cerebro del bot (con memoria) está en línea."