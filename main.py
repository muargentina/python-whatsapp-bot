import os
import json
import requests
import google.generativeai as genai
import openai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Cargar credenciales desde variables de entorno
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configurar la API de OpenAI
openai.api_key = OPENAI_API_KEY

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Esta función se usa para la verificación inicial del Webhook por parte de Meta.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print('WEBHOOK_VERIFIED')
            return challenge, 200
        else:
            return 'VERIFICATION_FAILED', 403
    return 'INVALID_REQUEST', 400

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Esta función maneja los mensajes entrantes de WhatsApp.
    """
    body = request.get_json()
    print(json.dumps(body, indent=2))  # Para depuración

    try:
        # Extraer el mensaje del usuario
        if body.get('object'):
            if (body.get('entry') and
                    body['entry'][0].get('changes') and
                    body['entry'][0]['changes'][0].get('value') and
                    body['entry'][0]['changes'][0]['value'].get('messages') and
                    body['entry'][0]['changes'][0]['value']['messages'][0]):

                message_data = body['entry'][0]['changes'][0]['value']['messages'][0]
                from_number = message_data['from']
                user_message = message_data['text']['body']

                # 1. Obtener la respuesta de la IA
                ai_response = get_ai_response(user_message)

                                # --- LÍNEA DE DEPURACIÓN CRUCIAL ---
                print(f"INTENTANDO RESPONDER AL NÚMERO: '{from_number}'")
                # ------------------------------------

                # 2. Enviar la respuesta de vuelta al usuario
                send_whatsapp_message(from_number, ai_response)

            return jsonify({'status': 'ok'}), 200
    except Exception as e:
        print(f"Error handling webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

    return 'EVENT_RECEIVED', 200


# Carga la nueva clave de API al inicio
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def get_ai_response(message):
    """
    Llama a la API de Google Gemini para obtener una respuesta inteligente.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash') # Usamos el modelo más rápido y eficiente
        response = model.generate_content(message)
        return response.text
    except Exception as e:
        print(f"Error en Google Gemini: {e}")
        return "Lo siento, mi inteligencia (Gemini) no está respondiendo. Intenta más tarde."


def send_whatsapp_message(to_number, message):
    """
    Envía un mensaje de vuelta al usuario usando la API de WhatsApp.
    """
    # LA LÍNEA A CAMBIAR ES LA SIGUIENTE:
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"Respuesta de la API de WhatsApp: {response.status_code}, {response.text}")


if __name__ == '__main__':
    app.run(port=5000, debug=True)