import os
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

# Asegúrate de instalar Flask si no lo tienes: pip install Flask
# Y gunicorn para el despliegue: pip install gunicorn

app = Flask(__name__)

# --- Configuración ---
# Archivo donde se guardarán las claves (dentro del contenedor de Render)
# ATENCIÓN: En Render, los archivos en el disco son efímeros.
# Si el servicio se reinicia, los datos de este archivo se perderán.
# Para un uso en producción, se recomienda una base de datos persistente (como PostgreSQL en Render).
KEYS_FILE = 'keys.json'

# Clave de API para proteger las operaciones de escritura/borrado
# DEBE COINCIDIR CON LA API_KEY EN key_generator.py
API_KEY = "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789" # ¡IMPORTANTE: Cámbiala y que sea la misma que en key_generator.py!

# --- Funciones de Utilidad para el archivo JSON ---
def load_keys():
    """Carga las claves desde el archivo JSON."""
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("WARNING: keys.json is corrupted or empty. Starting with empty list.")
            return []
    return []

def save_keys(keys):
    """Guarda las claves en el archivo JSON."""
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

# --- Endpoints de la API ---

@app.route('/keys', methods=['GET'])
def get_keys():
    """Devuelve todas las claves."""
    keys = load_keys()
    return jsonify(keys)

@app.route('/keys', methods=['POST'])
def add_key():
    """Añade una nueva clave."""
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({"message": "Unauthorized"}), 401
    
    data = request.json
    if not data or 'key_string' not in data or 'expiration_date' not in data:
        return jsonify({"message": "Missing key_string or expiration_date"}), 400

    keys = load_keys()
    
    # Evitar claves duplicadas
    if any(k['key_string'] == data['key_string'] for k in keys):
        return jsonify({"message": "Key already exists"}), 409

    keys.append(data)
    save_keys(keys)
    return jsonify({"message": "Key added successfully", "key": data}), 201

@app.route('/keys/<string:key_string>', methods=['PUT'])
def update_key(key_string):
    """Actualiza la fecha de caducidad de una clave existente."""
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.json
    if not data or 'expiration_date' not in data:
        return jsonify({"message": "Missing expiration_date"}), 400
    
    keys = load_keys()
    found = False
    for i, key in enumerate(keys):
        if key['key_string'] == key_string:
            keys[i]['expiration_date'] = data['expiration_date']
            found = True
            break
    
    if found:
        save_keys(keys)
        return jsonify({"message": "Key updated successfully", "key_string": key_string}), 200
    else:
        return jsonify({"message": "Key not found"}), 404

@app.route('/keys/<string:key_string>', methods=['DELETE'])
def delete_key(key_string):
    """Elimina una clave."""
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({"message": "Unauthorized"}), 401

    keys = load_keys()
    initial_len = len(keys)
    keys = [key for key in keys if key['key_string'] != key_string]
    
    if len(keys) < initial_len:
        save_keys(keys)
        return jsonify({"message": "Key deleted successfully", "key_string": key_string}), 200
    else:
        return jsonify({"message": "Key not found"}), 404

# --- Endpoint de Verificación de Clave (para GENtickets.py) ---
@app.route('/verify_key/<string:key_string>', methods=['GET'])
def verify_key(key_string):
    """Verifica si una clave existe y está activa."""
    keys = load_keys()
    current_time = datetime.now()

    for key_data in keys:
        if key_data['key_string'] == key_string:
            try:
                # Parsear la fecha de caducidad del formato string a datetime object
                expiration_date = datetime.strptime(key_data['expiration_date'], '%Y-%m-%d %H:%M:%S')
                if current_time < expiration_date:
                    return jsonify({"valid": True, "message": "Key is active"}), 200
                else:
                    return jsonify({"valid": False, "message": "Key is expired"}), 200
            except ValueError:
                # Si la fecha no tiene el formato esperado
                return jsonify({"valid": False, "message": "Invalid expiration date format"}), 200
    
    return jsonify({"valid": False, "message": "Key not found"}), 200

# --- Inicio del Servidor ---
if __name__ == '__main__':
    # Render asigna un puerto a través de la variable de entorno PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)