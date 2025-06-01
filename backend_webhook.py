import os
import subprocess
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS # ¡Nuevo! Para manejar las cabeceras CORS

app = Flask(__name__)
CORS(app) # Habilita CORS para todas las rutas de tu aplicación Flask. Esto es necesario
          # si el formulario se envía directamente desde tu dominio web al backend.

# Render asigna un puerto a través de la variable de entorno PORT
port = int(os.environ.get("PORT", 10000))

# --- Ruta para el webhook de Formspree (Se mantiene por si el usuario aún lo usa o para compatibilidad) ---
# Si decides que tu formulario HTML ya NO usa Formspree, esta ruta podría volverse obsoleta.
@app.route('/webhook/purchase', methods=['POST'])
def handle_formspree_webhook():
    print("INFO:backend_webhook:Received webhook data from Formspree:", request.form)
    
    # Formspree envía datos como 'application/x-www-form-urlencoded', no JSON
    product_name = request.form.get('product_name')
    buyer_email = request.form.get('_replyto') # Formspree usa _replyto para el email
    discord_username = request.form.get('discord_username')
    paypal_url = request.form.get('paypal_url') # Aunque Formspree maneje la redirección, el dato llega aquí

    if not all([product_name, buyer_email, discord_username, paypal_url]):
        print("ERROR:backend_webhook:Missing data in Formspree webhook.")
        return jsonify({"status": "error", "message": "Missing data"}), 400

    try:
        # Aquí la clave se sigue generando ANTES del pago (por el webhook de Formspree)
        key_generator_command = [
            "python",
            "key_generator.py",
            "--action", "generate_for_purchase",
            "--product_name", product_name,
            "--buyer_email", buyer_email,
            "--discord_username", discord_username,
            "--api_key", "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789" # ¡IMPORTANTE: Asegúrate de que coincida con key_generator.py y backend_server.py!
        ]
        
        process = subprocess.run(key_generator_command, capture_output=True, text=True, check=True)
        print("INFO:backend_webhook:key_generator.py stdout:", process.stdout)
        print("INFO:backend_webhook:key_generator.py stderr:", process.stderr)

        if "Key generated successfully" in process.stdout:
            # Si el webhook funciona, Formspree (si sigue activo para este formulario)
            # manejará la redirección del usuario. Esta parte solo responde a Formspree.
            return jsonify({"status": "success", "message": "Webhook processed"}), 200
        else:
            print("ERROR:backend_webhook:Key generation failed from Formspree webhook.")
            return jsonify({"status": "error", "message": "Key generation failed"}), 500

    except subprocess.CalledProcessError as e:
        print(f"ERROR:backend_webhook:Key generator command failed from Formspree webhook: {e}")
        print(f"Stderr: {e.stderr}")
        return jsonify({"status": "error", "message": "Key generator command failed"}), 500
    except Exception as e:
        print(f"ERROR:backend_webhook:Unhandled exception in Formspree webhook: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# --- NUEVA RUTA PARA PROCESAR DIRECTAMENTE EL FORMULARIO DESDE EL NAVEGADOR ---
# Esta ruta recibirá directamente las peticiones POST de tu HTML.
@app.route('/process_purchase', methods=['POST'])
def process_purchase_form():
    print("INFO:backend_webhook:Received direct form submission:", request.form)

    # Los datos del formulario HTML se acceden a través de request.form
    product_name = request.form.get('product_name')
    buyer_email = request.form.get('_replyto') # Usa '_replyto' ya que así se llama en tu HTML
    discord_username = request.form.get('discord_username')
    paypal_url = request.form.get('paypal_url')

    if not all([product_name, buyer_email, discord_username, paypal_url]):
        print("ERROR:backend_webhook:Missing data in direct form submission.")
        return "Datos incompletos. Por favor, vuelve atrás y rellena todos los campos.", 400

    try:
        # Aquí la clave se sigue generando ANTES del pago
        # porque esta ruta se activa cuando el usuario hace clic en "Continuar al Pago".
        key_generator_command = [
            "python",
            "key_generator.py",
            "--action", "generate_for_purchase",
            "--product_name", product_name,
            "--buyer_email", buyer_email,
            "--discord_username", discord_username,
            "--api_key", "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789" # ¡IMPORTANTE: Asegúrate de que coincida!
        ]
        
        process = subprocess.run(key_generator_command, capture_output=True, text=True, check=True)
        print("INFO:backend_webhook:key_generator.py stdout from direct form:", process.stdout)
        print("INFO:backend_webhook:key_generator.py stderr from direct form:", process.stderr)

        if "Key generated successfully" in process.stdout:
            # Si la clave se genera, redirige al usuario a PayPal
            print(f"INFO:backend_webhook:Redirecting to PayPal: {paypal_url}")
            return redirect(paypal_url) # ¡Esto redirige el navegador del usuario a la URL de PayPal!
        else:
            print("ERROR:backend_webhook:Key generation failed for direct form submission.")
            return "Error al generar la clave. Por favor, inténtalo de nuevo.", 500

    except subprocess.CalledProcessError as e:
        print(f"ERROR:backend_webhook:Key generator command failed for direct form: {e}")
        print(f"Stderr: {e.stderr}")
        return "Error interno al procesar la solicitud.", 500
    except Exception as e:
        print(f"ERROR:backend_webhook:Unhandled exception in direct form submission: {e}")
        return "Error interno inesperado.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)