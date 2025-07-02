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
    
    # --- AQUÍ CONSTRUYES EL PROMPT ---
    # Usamos comillas triples (""") para escribir un prompt de varias líneas de forma limpia.
    prompt = f"""
    **1. PERSONA:**
    Eres Atlas, el asistente virtual experto del servidor de juegos MU ARGENTINA , basado en el juego Online MU Online Season 6 Episodio 3. Tu tono es amigable, servicial y un poco entusiasta por el juego.

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

    **3. PREGUNTA DEL CLIENTE:**
    {message}
    """
    
    try:
        response = model.generate_content(prompt)
        print(f"🧠 Respuesta generada: '{response.text}'")
        return response.text
    except Exception as e:
        print(f"❌ Error en la llamada a Google Gemini: {e}")
        return "Lo siento, estoy teniendo un problema técnico para pensar mi respuesta."

@app.route('/')
def index():
    return "El cerebro del bot está en línea y configurado según la documentación oficial."