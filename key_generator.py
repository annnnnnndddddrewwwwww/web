import os
import datetime
import json
import uuid
import tkinter as tk
from tkinter import messagebox, filedialog

import customtkinter as ctk
import requests # Nuevo: Para hacer peticiones HTTP al servidor backend
import argparse
import sys
# Añade esto al inicio de tu archivo key_generator.py con tus otras importaciones
import argparse # Nueva importación

# --- Funciones de Gestión de Claves (Ahora interactúan con el backend) ---
# ... (todo el código que ya tienes para load_keys_from_server, add_key_to_server, etc.) ...

# --- CLASE DEL GENERADOR Y GESTOR DE CLAVES ---
# ... (todo el código de tu clase KeyGeneratorApp) ...

# --- Lógica para la ejecución desde línea de comandos (NUEVO) ---
def generate_key_cli(product_name, buyer_email, discord_username, api_key_from_webhook):
    """
    Genera una clave y la añade al servidor, diseñada para ser llamada desde la línea de comandos.
    """
    # Verifica que la API_KEY recibida del webhook coincida con la API_KEY interna
    if api_key_from_webhook != API_KEY:
        print("Error: API Key mismatch or invalid.")
        return False, "API Key mismatch or invalid."

    # Puedes ajustar la duración de la clave generada automáticamente aquí.
    # Por ejemplo, 30 días por defecto para las compras automáticas.
    duration_days = 30
    
    new_key_string = str(uuid.uuid4())
    expiration_date = datetime.datetime.now() + datetime.timedelta(days=duration_days)
    expiration_str = expiration_date.strftime('%Y-%m-%d %H:%M:%S')

    # Añadir la clave al servidor
    response_data = add_key_to_server(new_key_string, expiration_str)

    if response_data:
        print(f"Key generated successfully for purchase: {new_key_string}")
        print(f"Details: Product='{product_name}', Email='{buyer_email}', Discord='{discord_username}', Expires='{expiration_str}'")
        return True, f"Key generated: {new_key_string}"
    else:
        print("Error: Failed to save key to server from webhook.")
        return False, "Failed to save key to server from webhook."

# --- Bloque principal de ejecución del script (MODIFICADO) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Key Generator and Manager for Cast_Sneakers")
    parser.add_argument("--action", help="Action to perform: 'generate_for_purchase' or 'run_gui'")
    parser.add_argument("--product_name", help="Product name for key generation (CLI only)")
    parser.add_argument("--buyer_email", help="Buyer email for key generation (CLI only)")
    parser.add_argument("--discord_username", help="Discord username for key generation (CLI only)")
    parser.add_argument("--api_key", help="API Key for secure CLI operations")

    args = parser.parse_args()

    if args.action == "generate_for_purchase":
        if not all([args.product_name, args.buyer_email, args.discord_username, args.api_key]):
            print("Error: Missing arguments for 'generate_for_purchase' action.")
            parser.print_help()
        else:
            # Aquí es donde se llama la función generate_key_cli
            success, message = generate_key_cli(
                args.product_name,
                args.buyer_email,
                args.discord_username,
                args.api_key
            )
            if not success:
                print(f"CLI Key Generation failed: {message}")
    elif args.action == "run_gui":
        app = KeyGeneratorApp()
        app.mainloop()
    elif not args.action and (not args.product_name and not args.buyer_email and not args.discord_username and not args.api_key):
        # Si no se pasa ninguna acción y no hay argumentos de CLI, ejecuta la GUI por defecto
        app = KeyGeneratorApp()
        app.mainloop()
    else:
        print("Error: Invalid action or arguments provided.")
        parser.print_help()

# --- Rutas de las Carpetas (relativas al script del generador de claves) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Ya no necesitamos KEYS_FILE_PATH local, las claves residen en el servidor

# --- URL del Servidor Backend ---
# ¡IMPORTANTE! DEBES CAMBIAR ESTA URL si tu servidor no está en la misma máquina o usa otro puerto.
# Por ejemplo: "http://tu_ip_publica:5000"
SERVER_URL = "https://cast-sneakers-backend.onrender.com"

# --- Clave de API para proteger las operaciones de escritura (Generador) ---
# DEBE COINCIDIR CON LA API_KEY EN backend_server.py
API_KEY = "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789" # ¡IMPORTANTE: Cámbiala y que sea la misma que en el backend!

# --- Funciones de Gestión de Claves (Ahora interactúan con el backend) ---
def load_keys_from_server():
    """Carga las claves desde el servidor backend."""
    try:
        response = requests.get(f"{SERVER_URL}/keys")
        response.raise_for_status() # Lanza una excepción para errores HTTP (4xx o 5xx)
        return response.json()
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor de claves en {SERVER_URL}.\nAsegúrate de que el servidor está en funcionamiento.")
        print(f"🚨 ERROR: No se pudo conectar al servidor de claves en {SERVER_URL}.")
        return []
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de Red", f"Ocurrió un error al obtener las claves del servidor: {e}")
        print(f"🚨 ERROR de red al obtener claves del servidor: {e}")
        return []
    except json.JSONDecodeError:
        messagebox.showerror("Error del Servidor", "El servidor devolvió una respuesta inválida (no JSON).")
        print("🚨 ERROR: El servidor devolvió una respuesta no JSON.")
        return []

def add_key_to_server(key_string, expiration_date):
    """Añade una nueva clave al servidor backend."""
    headers = {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}
    payload = {"key_string": key_string, "expiration_date": expiration_date}
    try:
        response = requests.post(f"{SERVER_URL}/keys", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de API", f"Error al añadir clave al servidor: {e}\n{response.text if response else ''}")
        print(f"🚨 ERROR al añadir clave al servidor: {e}")
        return None

def update_key_on_server(key_string, new_expiration_date):
    """Actualiza la fecha de caducidad de una clave en el servidor backend."""
    headers = {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}
    payload = {"expiration_date": new_expiration_date}
    try:
        response = requests.put(f"{SERVER_URL}/keys/{key_string}", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de API", f"Error al actualizar clave en el servidor: {e}\n{response.text if response else ''}")
        print(f"🚨 ERROR al actualizar clave en el servidor: {e}")
        return None

def delete_key_from_server(key_string):
    """Elimina una clave del servidor backend."""
    headers = {'X-API-Key': API_KEY}
    try:
        response = requests.delete(f"{SERVER_URL}/keys/{key_string}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de API", f"Error al eliminar clave del servidor: {e}\n{response.text if response else ''}")
        print(f"🚨 ERROR al eliminar clave del servidor: {e}")
        return None

# --- CLASE DEL GENERADOR Y GESTOR DE CLAVES ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class KeyGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Generador y Gestor de Claves Cast_Sneakers")
        self.geometry("600x500") # Aumentado el tamaño para las nuevas funcionalidades
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)

        # Usar el parámetro 'command' para manejar el cambio de pestaña
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_changed_by_command)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tabview.add("Generar Clave")
        self.tabview.add("Gestionar Claves")

        # Configurar la pestaña "Generar Clave"
        self.setup_generate_tab()

        # Configurar la pestaña "Gestionar Claves"
        self.setup_manage_tab()

        # Variable para la clave seleccionada en la pestaña de gestión
        self.selected_key_data = None
        
        # Cargar las claves al iniciar la aplicación en la pestaña de gestión
        # Esto asegura que la lista se cargue al inicio si la pestaña de gestión es la predeterminada
        self.load_existing_keys()
        
    def on_tab_changed_by_command(self, selected_tab_name):
        """Callback que se ejecuta cuando se cambia de pestaña."""
        if selected_tab_name == "Gestionar Claves":
            self.load_existing_keys()

    def setup_generate_tab(self):
        generate_tab = self.tabview.tab("Generar Clave")
        generate_tab.grid_columnconfigure(0, weight=1)
        generate_tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(generate_tab, text="Generar Nueva Clave", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 20))

        ctk.CTkLabel(generate_tab, text="Duración de la clave (días):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.duration_entry = ctk.CTkEntry(generate_tab, placeholder_text="Número de días")
        self.duration_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.duration_entry.insert(0, "30") # Por defecto 30 días

        self.generate_button = ctk.CTkButton(generate_tab, text="Generar Nueva Clave", command=self.generate_new_key)
        self.generate_button.grid(row=2, column=0, columnspan=2, pady=20, sticky="ew", padx=10)

        ctk.CTkLabel(generate_tab, text="Clave Generada:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.generated_key_label = ctk.CTkLabel(generate_tab, text="", font=ctk.CTkFont(size=12, weight="bold"), wraplength=200)
        self.generated_key_label.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        self.copy_button = ctk.CTkButton(generate_tab, text="Copiar Clave", command=self.copy_key_to_clipboard, state="disabled")
        self.copy_button.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew", padx=10)

        self.status_label_generate = ctk.CTkLabel(generate_tab, text="", text_color="green")
        self.status_label_generate.grid(row=5, column=0, columnspan=2, pady=(0, 10))

    def setup_manage_tab(self):
        manage_tab = self.tabview.tab("Gestionar Claves")
        manage_tab.grid_rowconfigure(0, weight=1) # Permite que el scrollable frame se expanda
        manage_tab.grid_rowconfigure(1, weight=0) # Marco de edición
        manage_tab.grid_columnconfigure(0, weight=1)

        self.keys_list_frame = ctk.CTkScrollableFrame(manage_tab, label_text="Claves Existentes")
        self.keys_list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.keys_list_frame.grid_columnconfigure(0, weight=1) # Para que las claves se expandan

        self.edit_key_frame = ctk.CTkFrame(manage_tab)
        self.edit_key_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.edit_key_frame.grid_columnconfigure(1, weight=1) # Para que los campos de entrada se expandan

        ctk.CTkLabel(self.edit_key_frame, text="Clave Seleccionada:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.selected_key_label = ctk.CTkLabel(self.edit_key_frame, text="", wraplength=250, font=ctk.CTkFont(size=10, weight="bold"))
        self.selected_key_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.edit_key_frame, text="Nueva Fecha de Caducidad (YYYY-MM-DD HH:MM:SS):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.new_expiration_entry = ctk.CTkEntry(self.edit_key_frame, placeholder_text="Ej: 2025-12-31 23:59:59")
        self.new_expiration_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.update_key_button = ctk.CTkButton(self.edit_key_frame, text="Actualizar Clave", command=self.update_selected_key)
        self.update_key_button.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew", padx=5)

        self.delete_key_button = ctk.CTkButton(self.edit_key_frame, text="Eliminar Clave Seleccionada", fg_color="red", hover_color="darkred", command=self.delete_selected_key)
        self.delete_key_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew", padx=5)

        self.status_label_manage = ctk.CTkLabel(manage_tab, text="", text_color="green")
        self.status_label_manage.grid(row=2, column=0, pady=(0, 10))


    def generate_new_key(self):
        try:
            duration_days = int(self.duration_entry.get().strip())
            if duration_days <= 0:
                self.status_label_generate.configure(text_color="red", text="La duración debe ser un número positivo de días.")
                return

            new_key_string = str(uuid.uuid4()) # Genera una clave única
            expiration_date = datetime.datetime.now() + datetime.timedelta(days=duration_days)
            expiration_str = expiration_date.strftime('%Y-%m-%d %H:%M:%S')

            # Enviar la nueva clave al servidor
            response_data = add_key_to_server(new_key_string, expiration_str)

            if response_data:
                self.generated_key_label.configure(text=new_key_string)
                self.copy_button.configure(state="normal")
                self.status_label_generate.configure(text_color="green", text=f"Clave generada y guardada. Caduca: {expiration_date.strftime('%d/%m/%Y %H:%M:%S')}")
                messagebox.showinfo("Clave Generada", f"Nueva clave:\n{new_key_string}\n\nCaduca el: {expiration_date.strftime('%d/%m/%Y %H:%M:%S')}\n\nGuardada en el servidor.")
            else:
                self.status_label_generate.configure(text_color="red", text="Error al guardar la clave en el servidor.")
                messagebox.showerror("Error", "No se pudo guardar la clave en el servidor. Revisa la consola.")

        except ValueError:
            self.status_label_generate.configure(text_color="red", text="Por favor, introduce un número válido para la duración.")
        except Exception as e:
            self.status_label_generate.configure(text_color="red", text=f"Error inesperado al generar clave: {e}")
            print(f"🚨 ERROR inesperado al generar clave: {e}")
            import traceback
            traceback.print_exc()


    def copy_key_to_clipboard(self):
        key = self.generated_key_label.cget("text")
        if key:
            self.clipboard_clear()
            self.clipboard_append(key)
            self.status_label_generate.configure(text_color="blue", text="Clave copiada al portapapeles.")

    def load_existing_keys(self):
        # Limpiar widgets existentes en el scrollable frame
        for widget in self.keys_list_frame.winfo_children():
            widget.destroy()
        
        self.key_widgets = [] # Reiniciar la lista de referencias de widgets
        self.selected_key_data = None
        self.selected_key_label.configure(text="")
        self.new_expiration_entry.delete(0, ctk.END)
        self.new_expiration_entry.insert(0, "") # Limpiar el campo de fecha

        keys = load_keys_from_server() # Cargar claves desde el servidor
        if not keys:
            ctk.CTkLabel(self.keys_list_frame, text="No hay claves guardadas en el servidor.").pack(pady=10)
            return

        for i, key_data in enumerate(keys):
            key_string = key_data.get('key_string', 'N/A')
            expiration_str = key_data.get('expiration_date', 'N/A')

            key_frame = ctk.CTkFrame(self.keys_list_frame, fg_color="transparent")
            key_frame.pack(fill="x", pady=2, padx=5)
            key_frame.grid_columnconfigure(0, weight=1) # Key string
            key_frame.grid_columnconfigure(1, weight=0) # Select button

            # Mostrar estado de la clave
            current_time = datetime.datetime.now()
            status_text = ""
            status_color = "white" # Default for valid
            try:
                exp_date_obj = datetime.datetime.strptime(expiration_str, '%Y-%m-%d %H:%M:%S')
                if current_time < exp_date_obj:
                    status_text = " (ACTIVA)"
                    status_color = "green"
                else:
                    status_text = " (CADUCADA)"
                    status_color = "red"
            except ValueError:
                status_text = " (FECHA INVÁLIDA)"
                status_color = "orange"

            key_label_text = f"Clave: {key_string}\nCaduca: {expiration_str}{status_text}"
            key_label = ctk.CTkLabel(key_frame, text=key_label_text, justify="left", wraplength=350, text_color=status_color)
            key_label.grid(row=0, column=0, sticky="w")

            select_button = ctk.CTkButton(key_frame, text="Seleccionar", width=80,
                                          command=lambda k=key_data: self.select_key_for_edit(k))
            select_button.grid(row=0, column=1, padx=5, sticky="e")

            self.key_widgets.append((key_frame, key_label, select_button))
        
        self.status_label_manage.configure(text="") # Limpiar el estado de gestión

    def select_key_for_edit(self, key_data):
        self.selected_key_data = key_data
        self.selected_key_label.configure(text=key_data.get('key_string', 'N/A'))
        self.new_expiration_entry.delete(0, ctk.END)
        self.new_expiration_entry.insert(0, key_data.get('expiration_date', ''))
        self.status_label_manage.configure(text="Clave seleccionada para edición.", text_color="blue")

    def update_selected_key(self):
        if not self.selected_key_data:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una clave para actualizar.")
            return

        new_expiration_str = self.new_expiration_entry.get().strip()
        if not new_expiration_str:
            messagebox.showerror("Error", "La fecha de caducidad no puede estar vacía.")
            return

        try:
            # Validar formato de fecha
            datetime.datetime.strptime(new_expiration_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha y hora inválido. Usa YYYY-MM-DD HH:MM:SS")
            return

        # Actualizar la clave en el servidor
        response_data = update_key_on_server(self.selected_key_data.get('key_string'), new_expiration_str)

        if response_data:
            messagebox.showinfo("Éxito", "Clave actualizada correctamente en el servidor.")
            self.load_existing_keys() # Recargar la lista para mostrar los cambios
            self.selected_key_data = None # Limpiar la selección
            self.selected_key_label.configure(text="")
            self.new_expiration_entry.delete(0, ctk.END)
            self.status_label_manage.configure(text="Clave actualizada con éxito.", text_color="green")
        else:
            self.status_label_manage.configure(text="Error al actualizar la clave en el servidor.", text_color="red")


    def delete_selected_key(self):
        if not self.selected_key_data:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una clave para eliminar.")
            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar la clave:\n{self.selected_key_data.get('key_string')}?"):
            # Eliminar la clave del servidor
            response_data = delete_key_from_server(self.selected_key_data.get('key_string'))

            if response_data:
                messagebox.showinfo("Éxito", "Clave eliminada correctamente del servidor.")
                self.load_existing_keys() # Recargar la lista para mostrar los cambios
                self.selected_key_data = None # Limpiar la selección
                self.selected_key_label.configure(text="")
                self.new_expiration_entry.delete(0, ctk.END)
                self.status_label_manage.configure(text="Clave eliminada con éxito.", text_color="green")
            else:
                self.status_label_manage.configure(text="Error al eliminar la clave del servidor.", text_color="red")
        else:
            self.status_label_manage.configure(text="Eliminación de clave cancelada.", text_color="orange")


# --- Bloque principal de ejecución del generador de claves ---
if __name__ == "__main__":
    # If no command line arguments are provided (only the script name itself), run the GUI
    if len(sys.argv) == 1:
        app = KeyGeneratorApp()
        app.mainloop()
    else:
        # Command line argument parsing for non-GUI operations
        parser = argparse.ArgumentParser(description="Cast Sneakers Key Generator CLI Tool.")
        parser.add_argument('--action', type=str, required=True, choices=['generate_for_purchase'],
                            help="Action to perform: 'generate_for_purchase'.")
        parser.add_argument('--product_name', type=str, help="Name of the purchased product.")
        parser.add_argument('--buyer_email', type=str, help="Buyer's email address.")
        parser.add_argument('--discord_username', type=str, help="Buyer's Discord username.")
        parser.add_argument('--api_key', type=str, required=True, help="API Key for authentication.")

        args = parser.parse_args()

        if args.action == "generate_for_purchase":
            if not all([args.product_name, args.buyer_email, args.discord_username]):
                print("Error: For 'generate_for_purchase', --product_name, --buyer_email, and --discord_username are required.", file=sys.stderr)
                sys.exit(1)
            success, message = generate_key_cli(
                args.product_name,
                args.buyer_email,
                args.discord_username,
                args.api_key
            )
            if not success:
                print(f"Operation failed: {message}", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"Operation successful: {message}")
                sys.exit(0)
        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            sys.exit(1)
# --- NUEVA FUNCIÓN PARA GENERACIÓN DE CLAVES POR LÍNEA DE COMANDOS ---
def generate_key_cli(product_name, buyer_email, discord_username, api_key_from_caller):
    """
    Generates a key and adds it to the server.
    This function is designed to be called from the command line or another script.
    """
    # Asegúrate de que API_KEY esté definido globalmente en tu key_generator.py
    # Por ejemplo: API_KEY = "MiClaveSuperSecretaParaCastSneakers_2025!XYZ789"
    if api_key_from_caller != API_KEY:
        print("Error: API Key mismatch or invalid.", file=sys.stderr)
        return False, "API Key invalid."

    try:
        new_key = str(uuid.uuid4())
        # Example: Key expires in 30 days. Adjust as needed.
        expiration_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')

        key_data = {
            "key_string": new_key,
            "generated_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "expiration_date": expiration_date,
            "is_active": True,
            "product_name": product_name, # New fields
            "buyer_email": buyer_email,   # New fields
            "discord_username": discord_username, # New fields
            "notes": f"Generated for purchase of {product_name} by {buyer_email} ({discord_username})"
        }

        # Asegúrate de que add_key_to_server() esté definida y funcione correctamente
        response_data = add_key_to_server(key_data)

        if response_data and response_data.get("status") == "success":
            print(f"Key generated successfully for {buyer_email} ({discord_username}): {new_key}")
            print(f"Details: Product='{product_name}', Expires='{expiration_date}'")
            # IMPORTANTE: Aquí es donde querrías añadir tu lógica de envío de correo electrónico
            # por ejemplo: send_key_via_email(buyer_email, new_key, product_name)
            return True, "Key generated and stored."
        else:
            error_message = response_data.get("message", "Unknown error when adding key to server.")
            print(f"Error adding key to server: {error_message}", file=sys.stderr)
            return False, f"Error adding key to server: {error_message}"

    except Exception as e:
        print(f"An unexpected error occurred during key generation: {e}", file=sys.stderr)
        return False, f"Unexpected error: {str(e)}"