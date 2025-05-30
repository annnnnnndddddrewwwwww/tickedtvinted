from flask import Flask, request, jsonify
import json
import os
import datetime

app = Flask(__name__)

# --- Configuración del Servidor ---
SERVER_PORT = 5000 # Puerto en el que el servidor escuchará
# Ruta para el archivo de claves en el servidor
# Se guarda en la misma carpeta que el script del servidor para este ejemplo.
SERVER_KEYS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_keys.json")

# --- Clave de API para proteger las operaciones de escritura (Generador) ---
# CAMBIA ESTO POR UNA CLAVE SECRETA Y SEGURA EN UN ENTORNO REAL
API_KEY = "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789" # ¡IMPORTANTE: Cámbiala!

# --- Funciones de gestión de claves para el servidor ---
def load_server_keys():
    """Carga las claves desde el archivo server_keys.json del servidor."""
    if not os.path.exists(SERVER_KEYS_FILE):
        return []
    try:
        with open(SERVER_KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Advertencia: El archivo '{SERVER_KEYS_FILE}' está vacío o corrupto. Inicializando.")
        save_server_keys([]) # Inicializar con una lista vacía
        return []

def save_server_keys(keys):
    """Guarda las claves en el archivo server_keys.json del servidor."""
    with open(SERVER_KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keys, f, indent=4)

# --- Autenticación básica para API ---
def authenticate_request():
    """Verifica la clave de API en el encabezado X-API-Key."""
    api_key_header = request.headers.get('X-API-Key')
    if api_key_header == API_KEY:
        return True
    return False

# --- Endpoints de la API ---

@app.route('/keys', methods=['GET'])
def get_all_keys():
    """Endpoint para que la aplicación cliente obtenga todas las claves."""
    keys = load_server_keys()
    # No es necesario autenticar esta solicitud GET para este ejemplo simplificado
    # En un entorno real, podrías querer un token de sesión o una clave de acceso.
    return jsonify(keys), 200

@app.route('/keys', methods=['POST'])
def add_key():
    """Endpoint para añadir una nueva clave (usado por el generador)."""
    if not authenticate_request():
        return jsonify({"message": "Acceso no autorizado."}), 401

    data = request.get_json()
    if not data or 'key_string' not in data or 'expiration_date' not in data:
        return jsonify({"message": "Datos de clave incompletos. Se requieren 'key_string' y 'expiration_date'."}), 400

    new_key = {
        "key_string": data['key_string'],
        "expiration_date": data['expiration_date']
    }

    keys = load_server_keys()
    # Evitar claves duplicadas por key_string
    if any(k['key_string'] == new_key['key_string'] for k in keys):
        return jsonify({"message": "La clave ya existe."}), 409 # Conflict

    keys.append(new_key)
    save_server_keys(keys)
    print(f"Clave añadida por API: {new_key['key_string']} (Caduca: {new_key['expiration_date']})")
    return jsonify({"message": "Clave añadida correctamente.", "key": new_key}), 201 # Created

@app.route('/keys/<string:key_str>', methods=['PUT'])
def update_key(key_str):
    """Endpoint para actualizar una clave existente por su key_string (usado por el generador)."""
    if not authenticate_request():
        return jsonify({"message": "Acceso no autorizado."}), 401

    data = request.get_json()
    if not data or 'expiration_date' not in data:
        return jsonify({"message": "Datos de actualización incompletos. Se requiere 'expiration_date'."}), 400

    keys = load_server_keys()
    found = False
    for i, key_data in enumerate(keys):
        if key_data.get('key_string') == key_str:
            keys[i]['expiration_date'] = data['expiration_date']
            found = True
            break

    if found:
        save_server_keys(keys)
        print(f"Clave actualizada por API: {key_str} (Nueva caducidad: {data['expiration_date']})")
        return jsonify({"message": "Clave actualizada correctamente.", "key_string": key_str}), 200
    else:
        return jsonify({"message": "Clave no encontrada."}), 404

@app.route('/keys/<string:key_str>', methods=['DELETE'])
def delete_key(key_str):
    """Endpoint para eliminar una clave por su key_string (usado por el generador)."""
    if not authenticate_request():
        return jsonify({"message": "Acceso no autorizado."}), 401

    keys = load_server_keys()
    initial_len = len(keys)
    keys = [k for k in keys if k.get('key_string') != key_str]

    if len(keys) < initial_len:
        save_server_keys(keys)
        print(f"Clave eliminada por API: {key_str}")
        return jsonify({"message": "Clave eliminada correctamente.", "key_string": key_str}), 200
    else:
        return jsonify({"message": "Clave no encontrada."}), 404

# --- Inicio del Servidor ---
if __name__ == '__main__':
    print(f"Iniciando servidor Flask en http://127.0.0.1:{SERVER_PORT}")
    print(f"Archivo de claves del servidor: {SERVER_KEYS_FILE}")
    print(f"Clave API para generador: {API_KEY}") # ¡RECUERDA CAMBIAR ESTA CLAVE!
    # Usa el puerto de entorno si está disponible (para producción), si no, usa 5000 (para local)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)