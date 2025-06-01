# backend_webhook.py

# --- IMPORTS ---
import os
import subprocess
from flask import Flask, request, jsonify
import logging # Importa el módulo de logging

# Configura el logger para que se muestren mensajes INFO y superiores
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- APP CONFIGURATION ---

# Configura esto para que coincida con tu clave en key_generator.py
# ES CRUCIAL QUE ESTA CLAVE SEA LA MISMA en key_generator.py Y en las Variables de Entorno de Render.
# Si vas a usar variables de entorno en Render (lo más seguro), asegúrate de que el nombre de la KEY
# en Render sea "KEY_GENERATOR_API_KEY".
# El segundo argumento de .get() es un valor por defecto si la variable de entorno no se encuentra (útil para pruebas locales).
KEY_GENERATOR_API_KEY = os.environ.get("KEY_GENERATOR_API_KEY", "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789")
# Si decidiste usar otra clave, reemplaza "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789" con la tuya.


# --- ROUTES ---

@app.route('/webhook/purchase', methods=['POST'])
def handle_purchase_webhook():
    """
    Maneja las peticiones POST del formulario de compra de la web.
    Recibe los datos del formulario (no JSON) y llama a key_generator.py.
    """
    # Obtén los datos del formulario (form-data)
    product_name = request.form.get('product_name')
    buyer_email = request.form.get('_replyto') # El nombre del campo en tu HTML es _replyto
    discord_username = request.form.get('discord_username')
    paypal_url = request.form.get('paypal_url') # Captura la URL de PayPal

    # Verifica que los campos necesarios estén presentes
    if not all([product_name, buyer_email, discord_username, paypal_url]):
        app.logger.error("Missing required fields: product_name, buyer_email, discord_username, or paypal_url")
        return jsonify({"status": "error", "message": "Missing required form fields"}), 400

    app.logger.info(f"Received webhook data: Product={product_name}, Email={buyer_email}, Discord={discord_username}, PayPal_URL={paypal_url}")

    # Construye la ruta al script key_generator.py
    # os.path.dirname(os.path.abspath(__file__)) obtiene el directorio del script actual.
    key_generator_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key_generator.py')

    # Prepara el comando para ejecutar key_generator.py como un subproceso
    command = [
        "python",
        key_generator_path,
        "--action", "generate_for_purchase",
        "--product_name", product_name,
        "--buyer_email", buyer_email,
        "--discord_username", discord_username,
        "--api_key", KEY_GENERATOR_API_KEY # Pasa la API Key como argumento
    ]

    # Para depuración: registra el comando completo que se ejecutará
    app.logger.info(f"Executing key generator command: {' '.join(command)}")

    try:
        # Ejecuta el script key_generator.py
        # capture_output=True: captura stdout y stderr
        # text=True: decodifica stdout/stderr como texto
        # check=True: si el proceso devuelve un código de salida distinto de 0, lanza CalledProcessError
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Captura y registra la salida estándar y de error del script key_generator.py
        app.logger.info(f"key_generator.py stdout: {result.stdout}")
        if result.stderr:
            app.logger.error(f"key_generator.py stderr: {result.stderr}")

        # Si el script se ejecutó con éxito (código de salida 0)
        if result.returncode == 0:
            return jsonify({"status": "success", "message": "Key generation initiated successfully", "redirect_url": paypal_url}), 200
        else:
            # Si el script devolvió un error
            app.logger.error(f"key_generator.py failed with exit code {result.returncode}. Stderr: {result.stderr}")
            return jsonify({"status": "error", "message": "Key generation failed", "details": result.stderr, "redirect_url": paypal_url}), 500

    except subprocess.CalledProcessError as e:
        # Se lanza si check=True y el subproceso devuelve un error
        app.logger.error(f"Error executing key_generator.py (CalledProcessError): {e.stderr}")
        return jsonify({"status": "error", "message": "Server error during key generation", "details": e.stderr, "redirect_url": paypal_url}), 500
    except FileNotFoundError:
        # Se lanza si 'python' o 'key_generator.py' no se encuentran
        app.logger.error(f"key_generator.py not found at {key_generator_path}. Check file path.")
        return jsonify({"status": "error", "message": "Key generator script not found on server", "redirect_url": paypal_url}), 500
    except Exception as e:
        # Para cualquier otro error inesperado
        app.logger.error(f"An unexpected error occurred in webhook handler: {e}")
        return jsonify({"status": "error", "message": "An unexpected server error occurred", "details": str(e), "redirect_url": paypal_url}), 500


# Ruta raíz simple para que Render.com no dé 404 en las comprobaciones de salud iniciales
@app.route('/', methods=['GET'])
def home():
    return "Cast Sneakers Webhook Service is running!", 200


# --- MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    # Cuando se ejecuta localmente, usa debug=True para más información
    # En Render, el puerto será proporcionado por la variable de entorno PORT
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))