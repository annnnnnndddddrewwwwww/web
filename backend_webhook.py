# backend_webhook.py
from flask import Flask, request, jsonify
import subprocess
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# IMPORTANT: This MUST MATCH the API_KEY in your key_generator.py
# For better security in production, read this from an environment variable on Render
KEY_GENERATOR_API_KEY = os.environ.get("KEY_GENERATOR_API_KEY", "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789")

# Path to your key_generator.py script
# This assumes backend_webhook.py and key_generator.py are in the same directory
KEY_GENERATOR_SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'key_generator.py'))

@app.route('/webhook/purchase', methods=['POST'])
def handle_purchase_webhook():
    if not request.is_json:
        logging.warning("Received non-JSON webhook data.")
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

    data = request.json
    logging.info(f"Received webhook data: {data}")

    # Extract required fields from form submission
    # Formspree uses '_replyto' for the email field by default if you use 'name="_replyto"'
    # If you change your HTML form action to your new backend directly,
    # the name for email will be 'buyer_email' (from your HTML input name="buyer_email")
    # Adapt this based on how you submit the form.
    # Since we are changing the form's `action` to POST directly to Flask,
    # it will typically be `request.form` for form-urlencoded or `request.json` if you use JavaScript to send JSON.
    # Your current HTML form uses `method="POST"`, which usually means `application/x-www-form-urlencoded`
    # or `multipart/form-data`. So `request.form` might be more appropriate.
    # Let's adjust to `request.form` for HTML form POST.
    # NOTE: If you plan to send JSON using JavaScript `fetch` API, then `request.json` is correct.
    # For a simple HTML form POST, `request.form` is generally what you get.

    # Let's assume for simplicity you'll adjust the HTML form to send JSON via JavaScript,
    # or ensure Formspree sends JSON to make `request.json` work.
    # If you stick to simple HTML form POST, change `request.json` to `request.form` below
    # and adjust field names from '_replyto' to 'buyer_email' accordingly.

    # Based on your HTML: <input type="email" id="buyer_email" name="_replyto" ...>
    # If you post directly to your Flask app, `name="_replyto"` will arrive as `_replyto`.
    # Let's assume `request.json` for Formspree-like JSON webhook, or if you will use JS fetch.
    # If you remove Formspree and directly POST the HTML form, it would be `request.form`.
    # To be safe, we'll try to get from both or standardize.

    # For now, let's keep `request.json` as it was based on the Formspree webhook concept.
    # If your HTML form posts directly, you'll need to change `data = request.json` to `data = request.form.to_dict()`.
    # And then change `_replyto` to `buyer_email`.

    # Let's try to parse based on common web form submission (form-urlencoded) first, as it's an HTML POST form.
    # If you send JSON, you'd use request.json. Your HTML form will send `application/x-www-form-urlencoded`.
    product_name = data.get('product_name') # This comes from hidden input
    buyer_email = data.get('buyer_email')   # This comes from buyer_email input
    discord_username = data.get('discord_username') # This comes from discord_username input

    # IMPORTANT: If you change your HTML form action directly to Flask,
    # the data will be in `request.form`, not `request.json`.
    # Let's modify the Flask app to handle `request.form` if it's not JSON, which is more robust for direct HTML form POST.
    if request.is_json:
        data_to_process = request.json
    else:
        # Assuming standard form-urlencoded POST
        data_to_process = request.form.to_dict()

    logging.info(f"Processing data: {data_to_process}")

    # Extract required fields (now using the direct HTML form names if not JSON, or JSON names)
    product_name = data_to_process.get('product_name')
    buyer_email = data_to_process.get('buyer_email') # Changed from _replyto if direct POST
    discord_username = data_to_process.get('discord_username')

    if not all([product_name, buyer_email, discord_username]):
        logging.error(f"Missing required fields: product_name={product_name}, buyer_email={buyer_email}, discord_username={discord_username}")
        return jsonify({"status": "error", "message": "Missing required form fields"}), 400

    # Construct the command to call key_generator.py
    command = [
        'python',
        KEY_GENERATOR_SCRIPT_PATH,
        '--action', 'generate_for_purchase',
        '--product_name', product_name,
        '--buyer_email', buyer_email,
        '--discord_username', discord_username,
        '--api_key', KEY_GENERATOR_API_KEY
    ]
    logging.info(f"Executing key generator command: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        logging.info(f"key_generator.py stdout: {result.stdout}")
        logging.info(f"key_generator.py stderr: {result.stderr}")

        # This response goes back to the client/browser that submitted the form.
        # After successful key generation, you might want to redirect the user to PayPal or a confirmation page.
        # For an HTML form POST, you'd typically redirect or render a new page.
        # jsonify is more for API endpoints.
        # For a simple POST, you could:
        # return "<script>window.location.href='" + data_to_process.get('paypal_url') + "';</script>"
        # Or, if you want a JSON response and then handle redirection with JavaScript:
        # You'll need to modify your `script.js` to send the form data with `fetch` and handle the response.

        # For the simplest approach: let's assume the form submission is purely for key generation,
        # and the PayPal redirection happens separately (e.g., using JS after successful key generation notification).
        # However, your current HTML shows the PayPal URL is a hidden input.
        # The best way to handle PayPal is to redirect the user to it *after* they submit the form.

        # Let's adjust the response to immediately redirect to PayPal after the key is generated.
        paypal_redirect_url = data_to_process.get('paypal_url')
        if paypal_redirect_url:
            logging.info(f"Redirecting to PayPal: {paypal_redirect_url}")
            return f"<script>window.location.href='{paypal_redirect_url}';</script>"
        else:
            logging.warning("PayPal URL not found in form data. Not redirecting.")
            return jsonify({"status": "success", "message": "Key generation process initiated. No PayPal URL for redirection."}), 200

    except subprocess.CalledProcessError as e:
        logging.error(f"key_generator.py failed with exit code {e.returncode}. Stderr: {e.stderr}, Stdout: {e.stdout}")
        return jsonify({"status": "error", "message": "Key generation failed", "details": e.stderr.strip()}), 500
    except Exception as e:
        logging.exception("An unexpected error occurred in webhook handler:")
        return jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    # For local testing, run on http://localhost:5001
    app.run(debug=True, port=5001)