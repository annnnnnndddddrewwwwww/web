import os
import datetime
import smtplib
import threading # Para el envío de emails en segundo plano
import tkinter as tk
from tkinter import messagebox, filedialog
import json # Para manejar el archivo de claves (se usará en funciones importadas)
import requests # Nuevo: Para hacer peticiones HTTP al servidor backend

import customtkinter as ctk # Importamos customtkinter
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email import encoders

from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from pdf2image import convert_from_path # Para convertir PDF a imagen para email

# --- CONFIGURACIÓN GLOBAL DEL TICKET ---
TICKET_WIDTH = 80 * mm
TICKET_MAX_HEIGHT = 300 * mm

MARGIN_X = 5 * mm
MARGIN_TOP = 10 * mm
MARGIN_BOTTOM = 5 * mm

# --- Rutas de las Carpetas (ahora relativas al script principal) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "Archivos necesarios")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "Clientes")

LOGO_FILE_PATH = os.path.join(ASSETS_DIR, "image.png")

# Paleta de colores: ¡Todo negro ahora!
COLOR_PRIMARY = colors.black
COLOR_SECONDARY = colors.black
COLOR_ACCENT = colors.black

# --- REGISTRO DE FUENTES PERSONALIZADAS ---
FONT_ROBOTO_REGULAR = os.path.join(ASSETS_DIR, 'Roboto-Regular.ttf')
FONT_ROBOTO_BOLD = os.path.join(ASSETS_DIR, 'Roboto-Bold.ttf')
FONT_ROBOTO_ITALIC = os.path.join(ASSETS_DIR, 'Roboto-Italic.ttf')
FONT_ROBOTO_BOLD_ITALIC = os.path.join(ASSETS_DIR, 'Roboto-BoldItalic.ttf')

try:
    pdfmetrics.registerFont(TTFont('Roboto-Regular', FONT_ROBOTO_REGULAR))
    pdfmetrics.registerFont(TTFont('Roboto-Bold', FONT_ROBOTO_BOLD))
    pdfmetrics.registerFont(TTFont('Roboto-Italic', FONT_ROBOTO_ITALIC))
    pdfmetrics.registerFont(TTFont('Roboto-BoldItalic', FONT_ROBOTO_BOLD_ITALIC))
    print("✅ Fuentes 'Roboto' registradas con éxito desde la carpeta 'Archivos necesarios'.")

    FONT_NORMAL = 'Roboto-Regular'
    FONT_BOLD = 'Roboto-Bold'
    FONT_ITALIC = 'Roboto-Italic'
    FONT_BOLD_ITALIC = 'Roboto-BoldItalic'

except Exception as e:
    print(f"🚨 ERROR: No se pudieron cargar las fuentes 'Roboto' desde '{ASSETS_DIR}'.")
    print(f"   Detalle del error: {e}")
    print("   Asegúrate de que los archivos .ttf (Roboto-Regular.ttf, etc.) están en esa carpeta.")
    print("   Usando fuentes predeterminadas de ReportLab (Helvetica) como respaldo.")
    FONT_NORMAL = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    FONT_ITALIC = 'Helvetica-Oblique'
    FONT_BOLD_ITALIC = 'Helvetica-BoldOblique'

# --- Banderas de Depuración para Imágenes ---
DEBUG_IMAGE_LOADING = False
DEBUG_RECTANGLE_PLACEHOLDERS = False

# --- CONFIGURACIÓN DE CORREO ELECTRÓNICO (¡IMPORTANTE: CONFIGURA ESTO!) ---
# Para Gmail, necesitarás generar una "contraseña de aplicación" si tienes 2FA activado.
# https://support.google.com/accounts/answer/185833
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "castsneakers@gmail.com"  # ¡CÁMBIAME! Tu dirección de correo
SENDER_PASSWORD = "groi vvdx msrh rkma" # ¡CÁMBIAME! Tu contraseña de aplicación

# --- URL del Servidor Backend ---
# ¡IMPORTANTE! Si tu servidor Flask no está en la misma máquina o usa otro puerto,
# DEBES cambiar esta URL. Por ejemplo: "http://tu_ip_publica:5000"
SERVER_URL = "https://cast-sneakers-backend.onrender.com"

# --- Funciones de Gestión de Claves (Ahora interactúan con el backend) ---
def validate_key(input_key):
    """Valida si la clave introducida es correcta y no ha caducado
    consultando el servidor backend.
    """
    try:
        response = requests.get(f"{SERVER_URL}/keys")
        response.raise_for_status() # Lanza una excepción para errores HTTP (4xx o 5xx)
        keys = response.json()
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor de claves en {SERVER_URL}.\nAsegúrate de que el servidor está en funcionamiento.")
        print(f"🚨 ERROR: No se pudo conectar al servidor de claves en {SERVER_URL}.")
        return False
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de Red", f"Ocurrió un error al obtener las claves del servidor: {e}")
        print(f"🚨 ERROR de red al obtener claves del servidor: {e}")
        return False
    except json.JSONDecodeError:
        messagebox.showerror("Error del Servidor", "El servidor devolvió una respuesta inválida (no JSON).")
        print("🚨 ERROR: El servidor devolvió una respuesta no JSON.")
        return False

    current_time = datetime.datetime.now()
    for key_data in keys:
        if key_data.get('key_string') == input_key:
            expiration_str = key_data.get('expiration_date')
            if expiration_str:
                try:
                    expiration_date = datetime.datetime.strptime(expiration_str, '%Y-%m-%d %H:%M:%S')
                    if current_time < expiration_date:
                        return True # Clave válida y no caducada
                    else:
                        print(f"Clave '{input_key}' caducada el {expiration_date}.")
                        return False # Clave caducada
                except ValueError:
                    print(f"Error: Formato de fecha de caducidad inválido para la clave '{input_key}'.")
                    return False # Fecha mal formada
            else:
                print(f"Advertencia: Clave '{input_key}' sin fecha de caducidad. Considerada válida.")
                return True
    return False # Clave no encontrada

def get_key_details_from_server(key_string):
    """Obtiene los detalles de una clave específica desde el servidor backend."""
    try:
        response = requests.get(f"{SERVER_URL}/keys")
        response.raise_for_status()
        keys = response.json()
        for key_data in keys:
            if key_data.get('key_string') == key_string:
                return key_data
        return None # Clave no encontrada
    except requests.exceptions.RequestException as e:
        print(f"🚨 ERROR al obtener detalles de clave del servidor: {e}")
        return None
    except json.JSONDecodeError:
        print("🚨 ERROR: El servidor devolvió una respuesta inválida (no JSON) al pedir detalles de clave.")
        return None

# --- Función para Enviar Correo Electrónico ---
def enviar_ticket_por_correo(
    destinatario_email: str,
    pdf_path: str,
    numero_pedido: str,
    comprador: str,
    adjuntar_pdf_original_param: bool = False
):
    """
    Envía un ticket PDF por correo electrónico, con el ticket incrustado como imagen.
    """
    print(f"📧 Intentando enviar ticket a {destinatario_email}...")

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = destinatario_email
        msg['Subject'] = f"Tu ticket de compra de Cast_Sneakers - Pedido {numero_pedido}"

        # --- Parte de Texto Plano (para clientes de correo que no soportan HTML) ---
        text_body = f"""
¡Hola {comprador}ाइए

Esperamos que este correo te encuentre bien.

Adjunto encontrarás el ticket de compra de tu reciente pedido de Cast_Sneakers en Vinted, con número {numero_pedido}.

Nos alegra mucho que hayas elegido Cast_Sneakers para tus nueva ropa. ¡Gracias por tu confianza!

Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos a través del chat de Vinted.

¡Disfruta!

Saludos,

El equipo de Cast_Sneakers

(Si no puedes ver la imagen del ticket directamente, por favor, abre el archivo PDF adjunto.)
"""
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))

        # --- Parte HTML para incrustar la imagen del ticket ---
        image_bytes = None
        image_cid = 'ticket_image'
        try:
            print(f"   Convirtiendo '{pdf_path}' a imagen para incrustar...")
            images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
            if images:
                img_buffer = os.path.join(OUTPUT_DIR, f"temp_ticket_{os.path.basename(pdf_path).replace('.pdf', '.png')}")
                images[0].save(img_buffer, 'PNG')
                with open(img_buffer, 'rb') as f:
                    image_bytes = f.read()
                os.remove(img_buffer)
                print("   PDF convertido a imagen PNG temporalmente.")
            else:
                print("🚨 ADVERTENCIA: No se pudo convertir el PDF a imagen. El ticket solo se adjuntará.")

        except Exception as e:
            print(f"🚨 ERROR al convertir PDF a imagen para incrustar: {e}")
            print("   Asegúrate de que 'poppler' esté instalado y en tu PATH.")
            print("   El ticket se enviará solo como archivo adjunto y con texto plano.")
            import traceback
            traceback.print_exc()
            image_bytes = None

        html_body = f"""
<html>
  <body>
    <p>¡Hola {comprador}!</p>
    <p>Esperamos que este correo te encuentre bien.</p>
    <p>Aquí tienes un resumen visual de tu ticket de compra de Cast_Sneakers en Vinted, con número <b>{numero_pedido}</b>:</p>
    <br>
    """
        if image_bytes:
            html_body += f'<img src="cid:{image_cid}" alt="Ticket de Compra Cast_Sneakers" style="max-width:100%; height:auto; display:block; margin: 0 auto;">'
        else:
            html_body += '<p>No se pudo mostrar la imagen del ticket directamente. Por favor, abre el archivo PDF adjunto.</p>'

        html_body += f"""
    <br>
    <p>Nos alegra mucho que hayas elegido Cast_Sneakers para tus nuevas zapatillas. ¡Gracias por tu confianza!</p>
    <p>Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos a través del chat de Vinted.</p>
    <p>¡Disfruta tus nuevas zapatillas!</p>
    <p>Saludos,</p>
    <p>El equipo de Cast_Sneakers</p>
  </body>
</html>
"""
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)

        # Si la imagen se generó, adjúntala como "inline" (incrustada)
        if image_bytes:
            image_part = MIMEImage(image_bytes, name=f"ticket_{numero_pedido}.png")
            image_part.add_header('Content-ID', f'<{image_cid}>')
            image_part.add_header('Content-Disposition', 'inline', filename=f"ticket_{numero_pedido}.png")
            msg.attach(image_part)
            print("   Imagen del ticket incrustada en el correo.")

        # --- Adjuntar el archivo PDF original (como respaldo) ---
        if adjuntar_pdf_original_param:
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(pdf_path)}",
            )
            msg.attach(part)
            print("   Archivo PDF adjunto al correo.")
        else:
            print("   Archivo PDF original no adjuntado (por elección del usuario).")


        # Conexión con el servidor SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print(f"   Conectando a {SMTP_SERVER}:{SMTP_PORT}...")
            server.starttls()
            print("   TLS iniciado. Intentando iniciar sesión...")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("   Sesión iniciada con éxito. Enviando mensaje...")
            server.send_message(msg)

        print(f"🎉 Ticket enviado con éxito a {destinatario_email}!")
    except smtplib.SMTPAuthenticationError:
        print(f"🚨 ERROR de autenticación al enviar el correo a {destinatario_email}.")
        print("   Asegúrate de que el correo y la contraseña de aplicación son correctos.")
        print("   Si usas Gmail con 2FA, necesitas una 'contraseña de aplicación'.")
    except smtplib.SMTPConnectError as e:
        print(f"🚨 ERROR de conexión SMTP al enviar el correo: {e}.")
        print("   Asegúrate de que SMTP_SERVER y SMTP_PORT son correctos y tu conexión a internet funciona.")
    except Exception as e:
        print(f"🚨 ERROR inesperado al enviar el correo a {destinatario_email}: {e}")
        import traceback
        traceback.print_exc()

# --- Función Principal para Generar el Ticket ---
def generar_ticket_venta_una_pagina(
    nombre_archivo: str,
    logo_path: str,
    numero_pedido_vinted: str,
    fecha_venta: str,
    comprador: str,
    articulos_vendidos: list[tuple[str, str, int, str]],
    precio_total: str
):
    """
    Genera un ticket de venta en formato PDF de una sola página, con un diseño profesional.
    Optimizado para la impresión en rollos de papel térmico, con logo como marca de agua.
    """
    full_output_path = os.path.join(OUTPUT_DIR, nombre_archivo)

    print(f"\n🚀 Generando ticket '{full_output_path}' con estilo cool (y Roboto!)...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"   Carpeta de salida '{OUTPUT_DIR}' verificada/creada.")

    c = canvas.Canvas(full_output_path, pagesize=(TICKET_WIDTH, TICKET_MAX_HEIGHT))
    print(f"   Canvas preparado: {TICKET_WIDTH/mm:.1f}mm x {TICKET_MAX_HEIGHT/mm:.1f}mm.")

    # 1. Dibujar la Marca de Agua (ANTES de todo lo demás)
    if DEBUG_IMAGE_LOADING: print(f"   Preparando marca de agua con logo desde: {logo_path}")
    try:
        if os.path.exists(logo_path):
            img_reader = ImageReader(logo_path)
            watermark_size = 15 * mm
            spacing = 5 * mm

            c.saveState()

            OPACIDAD_MARCA_AGUA = 0.20
            c.setFillAlpha(OPACIDAD_MARCA_AGUA)
            c.setStrokeAlpha(OPACIDAD_MARCA_AGUA)

            num_x = int(TICKET_WIDTH / (watermark_size + spacing)) + 1
            num_y = int(TICKET_MAX_HEIGHT / (watermark_size + spacing)) + 1

            for i in range(num_x):
                for j in range(num_y):
                    x_pos = i * (watermark_size + spacing)
                    y_pos = j * (watermark_size + spacing)

                    if DEBUG_RECTANGLE_PLACEHOLDERS:
                        c.setFillColor(colors.lightgrey)
                        c.rect(x_pos, y_pos, watermark_size, watermark_size, stroke=1, fill=1)
                    else:
                        c.drawImage(img_reader, x_pos, y_pos,
                                            width=watermark_size, height=watermark_size,
                                            mask='auto', preserveAspectRatio=True)

            c.restoreState()
            if DEBUG_IMAGE_LOADING: print(f"   Marca de agua dibujada con éxito (opacidad: {OPACIDAD_MARCA_AGUA*100:.0f}%).")
        else:
            print(f"🚨 ADVERTENCIA: Logo para marca de agua no encontrado en '{logo_path}'. La marca de agua no se dibujará.")
    except Exception as e:
        print(f"🚨 ERROR: No se pudo dibujar la marca de agua con el logo: {e}")
        import traceback
        traceback.print_exc()

    current_y = TICKET_MAX_HEIGHT - MARGIN_TOP

    # 2. Dibujar el Logo principal (arriba y centrado)
    if DEBUG_IMAGE_LOADING: print(f"   Intentando insertar logo principal desde: {logo_path}")
    try:
        if os.path.exists(logo_path):
            img_reader = ImageReader(logo_path)
            logo_width_mm = 30 * mm
            logo_height_mm = img_reader.getSize()[1] * (logo_width_mm / img_reader.getSize()[0])

            x_pos_logo = (TICKET_WIDTH - logo_width_mm) / 2

            if DEBUG_RECTANGLE_PLACEHOLDERS:
                c.setFillColor(colors.lightgrey)
                c.rect(x_pos_logo, current_y - logo_height_mm, logo_width_mm, logo_height_mm, stroke=1, fill=1)
            else:
                c.drawImage(img_reader, x_pos_logo, current_y - logo_height_mm,
                                width=logo_width_mm, height=logo_height_mm, mask='auto')
            current_y -= (logo_height_mm + 8 * mm)
            if DEBUG_IMAGE_LOADING: print("   Logo principal insertado con éxito.")
        else:
            c.setFillColor(colors.red)
            c.setFont(FONT_BOLD, 7)
            c.drawString(MARGIN_X, current_y - 5*mm, f"ERROR: LOGO PRINCIPAL NO ENCONTRADO EN '{logo_path}'")
            current_y -= (15 * mm)
            print(f"🚨 ERROR: El archivo de logo principal no existe en la ruta: '{logo_path}'")

    except Exception as e:
        c.setFillColor(colors.red)
        c.setFont(FONT_BOLD, 7)
        c.drawString(MARGIN_X, current_y - 5*mm, f"ERROR al cargar/dibujar logo principal: {e}")
        current_y -= (15 * mm)
        import traceback
        traceback.print_exc()

    # 3. Línea separadora decorativa
    c.setStrokeColor(COLOR_SECONDARY)
    c.setLineWidth(0.7)
    c.line(MARGIN_X, current_y, TICKET_WIDTH - MARGIN_X, current_y)
    current_y -= (6 * mm)

    # 4. Título y Slogan de la Empresa
    c.setFont(FONT_BOLD, 18)
    c.setFillColor(COLOR_PRIMARY)
    c.drawCentredString(TICKET_WIDTH / 2, current_y, "Cast_Sneakers")
    current_y -= (8 * mm)

    c.setFont(FONT_ITALIC, 9)
    c.setFillColor(COLOR_SECONDARY)
    c.drawCentredString(TICKET_WIDTH / 2, current_y, "Tu universo sneaker en Vinted")
    current_y -= (15 * mm)

    # 5. Detalles de la Venta
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(COLOR_PRIMARY)
    c.drawString(MARGIN_X, current_y, "--- DETALLES DE TU PEDIDO ---")
    current_y -= (7 * mm)

    c.setFont(FONT_NORMAL, 9)
    c.drawString(MARGIN_X, current_y, f"Nº Pedido Vinted: {numero_pedido_vinted}")
    current_y -= (4 * mm)
    c.drawString(MARGIN_X, current_y, f"Fecha de Compra: {fecha_venta}")
    current_y -= (4 * mm)
    c.drawString(MARGIN_X, current_y, f"Comprador: {comprador}")
    current_y -= (12 * mm)

    # 6. Artículos Vendidos con foto y cantidad
    c.setFont(FONT_BOLD, 11)
    c.drawString(MARGIN_X, current_y, "--- ARTÍCULO(S) ADQUIRIDO(S) ---")
    current_y -= (7 * mm)

    if not articulos_vendidos:
        c.setFont(FONT_ITALIC, 9)
        c.drawString(MARGIN_X + 5 * mm, current_y, "No se han listado artículos.")
        current_y -= (5 * mm)
    else:
        item_height = 18 * mm
        photo_size = 15 * mm
        text_offset_x = MARGIN_X + photo_size + 5*mm

        for articulo, talla, cantidad, ruta_imagen_producto in articulos_vendidos:
            image_x = MARGIN_X + 2*mm
            image_y = current_y - photo_size + 2*mm
            text_y = current_y - 8*mm

            if DEBUG_RECTANGLE_PLACEHOLDERS:
                c.setFillColor(colors.lightgrey)
                c.rect(image_x, image_y, photo_size, photo_size, stroke=1, fill=1)
                c.setFillColor(COLOR_PRIMARY)
            elif ruta_imagen_producto and os.path.exists(ruta_imagen_producto):
                try:
                    product_img_reader = ImageReader(ruta_imagen_producto)
                    c.drawImage(product_img_reader, image_x, image_y,
                                width=photo_size, height=photo_size, preserveAspectRatio=True, mask='auto')
                    if DEBUG_IMAGE_LOADING: print(f"   Imagen de producto '{articulo}' cargada desde: '{ruta_imagen_producto}'")
                except Exception as e:
                    print(f"🚨 ERROR: No se pudo cargar la imagen del producto '{articulo}' desde '{ruta_imagen_producto}': {e}")
                    c.setFillColor(colors.red)
                    c.setFont(FONT_BOLD, 6)
                    c.drawCentredString(image_x + photo_size/2, image_y + photo_size/2 + 2*mm, "IMAGEN NO")
                    c.drawCentredString(image_x + photo_size/2, image_y + photo_size/2 - 2*mm, "DISPONIBLE")
                    c.setStrokeColor(colors.red)
                    c.setLineWidth(0.5)
                    c.rect(image_x, image_y, photo_size, photo_size, stroke=1, fill=0)
                    c.setFillColor(COLOR_PRIMARY)
            else:
                c.setStrokeColor(COLOR_SECONDARY)
                c.setLineWidth(0.3)
                c.rect(image_x, image_y, photo_size, photo_size, stroke=1, fill=0)
                c.setFont(FONT_NORMAL, 6)
                c.setFillColor(COLOR_SECONDARY)
                c.drawCentredString(image_x + photo_size/2, image_y + photo_size/2, "No hay imagen")
                c.setFillColor(COLOR_PRIMARY)
                if DEBUG_IMAGE_LOADING: print(f"   No se proporcionó imagen o no existe para '{articulo}'.")


            c.setFont(FONT_BOLD, 10)
            c.setFillColor(COLOR_PRIMARY)
            c.drawString(text_offset_x, text_y, f"x{cantidad}")

            c.setFont(FONT_NORMAL, 9)
            c.setFillColor(COLOR_PRIMARY)
            c.drawString(text_offset_x + 10*mm, text_y, f"{articulo} (Talla: {talla})")

            current_y -= item_height
    current_y -= (5 * mm)

    # 7. Precio Total
    c.setFont(FONT_BOLD, 16)
    c.setFillColor(COLOR_ACCENT)
    c.drawRightString(TICKET_WIDTH - MARGIN_X, current_y, f"TOTAL: {precio_total} €")
    current_y -= (15 * mm)

    # 8. Línea divisoria
    c.setStrokeColor(COLOR_SECONDARY)
    c.setLineWidth(0.5)
    c.line(MARGIN_X, current_y, TICKET_WIDTH - MARGIN_X, current_y)
    current_y -= (8 * mm)

    # 9. Información Importante Adicional
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(COLOR_PRIMARY)
    c.drawCentredString(TICKET_WIDTH / 2, current_y, "INFORMACIÓN IMPORTANTE")
    current_y -= (6 * mm)

    textobject = c.beginText(MARGIN_X, current_y)
    textobject.setFont(FONT_NORMAL, 8)
    textobject.setFillColor(COLOR_SECONDARY)
    line_height = 9

    textobject.textLine("• Envíos: Todos los pedidos se gestionan mediante Vinted.")
    textobject.textLine("   Puedes seguir el estado de tu paquete en la app.")
    current_y -= line_height * 2

    textobject.textLine("• Contacto: Para cualquier duda o problema,")
    textobject.textLine("   por favor, escríbeme a través del chat de Vinted.")
    current_y -= line_height * 2

    textobject.textLine("• Valoración: Tu opinión es muy valiosa. Si todo es correcto,")
    textobject.textLine("   agradecería tu valoración positiva. En caso de incidencia,")
    textobject.textLine("   contacta antes de valorar para buscar una solución.")
    current_y -= line_height * 3

    c.drawText(textobject)
    current_y -= (15 * mm)

    # 10. Mensaje de Agradecimiento y Despedida
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(COLOR_ACCENT)
    c.drawCentredString(TICKET_WIDTH / 2, current_y, "¡Gracias por tu confianza!")
    current_y -= (8 * mm)

    c.setFont(FONT_ITALIC, 10)
    c.setFillColor(COLOR_PRIMARY)
    c.drawCentredString(TICKET_WIDTH / 2, current_y, "Esperamos verte pronto en Cast_Sneakers.")
    current_y -= (15 * mm)

    # 11. Guardar el PDF
    try:
        c.save()
        print(f"\n🎉 ¡Ticket '{full_output_path}' generado con éxito y con mucho estilo!")
        print(f"   Revisa la carpeta '{OUTPUT_DIR}' para encontrarlo.")
        return full_output_path
    except Exception as e:
        print(f"\n🔥 ERROR FATAL: No se pudo guardar el PDF '{full_output_path}'.")
        print(f"   Detalles del error: {e}")
        print(f"   Asegúrate de que el archivo no esté abierto y que tienes permisos de escritura en la carpeta '{OUTPUT_DIR}'.")
        import traceback
        traceback.print_exc()
        return None

# --- Función para obtener los datos de la venta (para uso directo del script, no para la web) ---
# Esta función ya no es necesaria si usas la interfaz web, pero la mantengo si la quieres para probar por consola.
# Para el entorno web, los datos vienen del frontend.
def obtener_datos_venta_por_consola():
    print("\n--- Datos de la Venta ---")
    num_pedido = input("Introduce el número de pedido de Vinted: ").strip()
    fecha = input("Introduce la fecha de venta (DD/MM/AAAA): ").strip()
    comprador = input("Introduce el nombre de usuario de Vinted del comprador: ").strip()

    articulos = []
    print("\n--- Artículos Vendidos ---")
    while True:
        nombre_articulo = input("Nombre del artículo (deja en blanco y pulsa Enter para terminar): ").strip()
        if not nombre_articulo:
            break
        talla_articulo = input(f"Talla de '{nombre_articulo}': ").strip()
        cantidad_articulo = int(input(f"Cantidad de '{nombre_articulo}' (por defecto 1): ") or "1")
        # Aquí la ruta de la imagen del producto se dejará como None para el ejemplo
        # Si tienes imágenes predefinidas por nombre, podrías usar un os.path.join(ASSETS_DIR, "imagen.png")
        articulos.append((nombre_articulo, talla_articulo, cantidad_articulo, None))

    precio = input("Introduce el precio total de la venta (ej. 25.50): ").strip()
    return num_pedido, fecha, comprador, articulos, precio

# --- CLASE DE LA APLICACIÓN CUSTOMTKINTER ---
ctk.set_appearance_mode("System")  # Modos: "System" (por defecto), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Temas: "blue" (por defecto), "green", "dark-blue"

class TicketGeneratorApp(ctk.CTk):
    def __init__(self, active_key_string: str): # Nuevo: Recibe la clave activa
        super().__init__()

        self.active_key_string = active_key_string # Guardamos la clave activa

        self.title("Cast_Sneakers - Generador de Tickets")
        self.geometry("800x700") # Altura aumentada para acomodar más elementos
        self.resizable(False, False) # Evitar el redimensionamiento para un diseño fijo

        # Configurar el diseño de la cuadrícula (4x1)
        self.grid_rowconfigure(0, weight=0) # Marco de cabecera
        self.grid_rowconfigure(1, weight=1) # Marco de contenido principal
        self.grid_rowconfigure(2, weight=0) # Marco de botones de acción
        self.grid_rowconfigure(3, weight=0) # Marco de estado
        self.grid_columnconfigure(0, weight=1)

        # --- Marcos ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0) # Columna para el estado de la clave

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1) # Dos columnas para el contenido principal

        self.button_frame = ctk.CTkFrame(self, corner_radius=10)
        self.button_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)

        self.status_frame = ctk.CTkFrame(self, corner_radius=10)
        self.status_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        # --- Widgets: Marco de Cabecera ---
        self.title_label = ctk.CTkLabel(self.header_frame, text="Generador de Tickets Cast_Sneakers",
                                        font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=10, sticky="w") # Alineado a la izquierda

        # Nuevo: Etiqueta para el estado de la clave
        self.key_status_label = ctk.CTkLabel(self.header_frame, text="Verificando clave...",
                                            font=ctk.CTkFont(size=12, weight="bold"),
                                            text_color="gray")
        self.key_status_label.grid(row=0, column=1, padx=10, pady=10, sticky="e") # Alineado a la derecha

        # --- Widgets: Marco Principal (Secciones de Entrada) ---

        # Columna Izquierda: Detalles del Pedido
        self.order_details_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.order_details_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.order_details_frame.grid_columnconfigure(1, weight=1) # Hacer que los campos de entrada se expandan

        ctk.CTkLabel(self.order_details_frame, text="Detalles del Pedido", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        ctk.CTkLabel(self.order_details_frame, text="Nº Pedido Vinted:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_pedido = ctk.CTkEntry(self.order_details_frame, placeholder_text="Ej: VINTED12345")
        self.entry_pedido.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.order_details_frame, text="Fecha de Compra:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_fecha = ctk.CTkEntry(self.order_details_frame, placeholder_text=datetime.date.today().strftime("%d/%m/%Y"))
        self.entry_fecha.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.entry_fecha.insert(0, datetime.date.today().strftime("%d/%m/%Y")) # Rellenar con la fecha actual

        ctk.CTkLabel(self.order_details_frame, text="Comprador:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_comprador = ctk.CTkEntry(self.order_details_frame, placeholder_text="Nombre de usuario Vinted")
        self.entry_comprador.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.order_details_frame, text="Precio Total (€):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.entry_precio = ctk.CTkEntry(self.order_details_frame, placeholder_text="Ej: 25.50")
        self.entry_precio.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Columna Derecha: Artículos
        self.items_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.items_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.items_frame.grid_columnconfigure(0, weight=1)
        self.items_frame.grid_columnconfigure(1, weight=0) # Para el botón de eliminar

        ctk.CTkLabel(self.items_frame, text="Artículos Adquiridos", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        self.item_entries = [] # Para almacenar la lista de (name_entry, size_entry, qty_entry, image_path_label, image_path)

        # MOVIDO: Definir add_item_button antes de llamar a add_item_row
        self.add_item_button = ctk.CTkButton(self.items_frame, text="+ Añadir Artículo", command=self.add_item_row)
        self.add_item_button.grid(row=999, column=0, columnspan=2, pady=(10, 0), sticky="ew") # Marcador de posición para añadir más filas

        self.add_item_row() # Añadir una fila de artículo inicial (ahora add_item_button ya existe)


        # --- Widgets: Marco de Botones (Acciones) ---
        self.generate_button = ctk.CTkButton(self.button_frame, text="Generar Ticket PDF", command=self.generate_ticket_action,
                                             font=ctk.CTkFont(size=14, weight="bold"))
        self.generate_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

        self.send_email_button = ctk.CTkButton(self.button_frame, text="Enviar Ticket por Email", command=self.open_email_dialog,
                                              font=ctk.CTkFont(size=14, weight="bold"))
        self.send_email_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.clear_button = ctk.CTkButton(self.button_frame, text="Limpiar Formulario", command=self.clear_form,
                                          fg_color="gray", hover_color="darkgray")
        self.clear_button.grid(row=0, column=2, padx=5, pady=10, sticky="ew")

        # --- Widgets: Marco de Estado ---
        self.status_label = ctk.CTkLabel(self.status_frame, text="Listo para generar tickets...", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # Variables para almacenar la ruta del PDF generado y las opciones de correo electrónico
        self.last_generated_pdf_path = None
        self.attach_pdf_original = ctk.BooleanVar(value=True) # Por defecto, adjuntar PDF

        # Iniciar la actualización del estado de la clave
        self.update_key_status_display() # Llamada inicial
        self.after(60000, self.update_key_status_display) # Programar la actualización cada minuto (60000 ms)


    def update_key_status_display(self):
        """
        Actualiza la etiqueta que muestra el estado y tiempo restante de la clave activa.
        """
        key_details = get_key_details_from_server(self.active_key_string)
        
        status_text = "Estado de Clave: "
        text_color = "gray"

        if key_details:
            expiration_str = key_details.get('expiration_date')
            if expiration_str:
                try:
                    expiration_date = datetime.datetime.strptime(expiration_str, '%Y-%m-%d %H:%M:%S')
                    current_time = datetime.datetime.now()
                    
                    if current_time < expiration_date:
                        remaining_time = expiration_date - current_time
                        days = remaining_time.days
                        hours = remaining_time.seconds // 3600
                        minutes = (remaining_time.seconds % 3600) // 60

                        if days > 0:
                            status_text += f"ACTIVA, Caduca en {days} días, {hours}h {minutes}m"
                        elif hours > 0:
                            status_text += f"ACTIVA, Caduca en {hours}h {minutes}m"
                        elif minutes > 0:
                            status_text += f"ACTIVA, Caduca en {minutes}m"
                        else:
                            status_text += "ACTIVA, Caduca en menos de 1 minuto"
                        text_color = "green"
                        
                        if remaining_time < datetime.timedelta(days=7): # Alerta si quedan menos de 7 días
                            text_color = "orange"
                            status_text += " (¡Pronto a caducar!)"

                    else:
                        status_text += "CADUCADA"
                        text_color = "red"
                except ValueError:
                    status_text += "ERROR (Fecha Inválida)"
                    text_color = "red"
            else:
                status_text += "ACTIVA (Sin fecha de caducidad)"
                text_color = "blue"
        else:
            status_text += "No Encontrada o Error de Conexión"
            text_color = "red"
            
        self.key_status_label.configure(text=status_text, text_color=text_color)
        
        # Reprogramar la actualización para el próximo minuto
        self.after(60000, self.update_key_status_display)


    def add_item_row(self):
        row_num = len(self.item_entries) + 1 # Empezar desde la fila 1 (la fila 0 es la cabecera)
        item_frame = ctk.CTkFrame(self.items_frame, fg_color="transparent")
        item_frame.grid(row=row_num, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        item_frame.grid_columnconfigure(0, weight=1) # Nombre
        item_frame.grid_columnconfigure(1, weight=0) # Talla
        item_frame.grid_columnconfigure(2, weight=0) # Cantidad
        item_frame.grid_columnconfigure(3, weight=0) # Botón de imagen
        item_frame.grid_columnconfigure(4, weight=0) # Botón de eliminar

        name_entry = ctk.CTkEntry(item_frame, placeholder_text="Nombre del artículo")
        name_entry.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        size_entry = ctk.CTkEntry(item_frame, placeholder_text="Talla")
        size_entry.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        qty_entry = ctk.CTkEntry(item_frame, width=50, placeholder_text="Cant.")
        qty_entry.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        qty_entry.insert(0, "1") # Cantidad por defecto

        image_path_var = tk.StringVar(value="") # Almacena la ruta de la imagen
        image_button = ctk.CTkButton(item_frame, text="Imagen", width=70,
                                     command=lambda var=image_path_var: self.select_image_path(var))
        image_button.grid(row=0, column=3, padx=2, pady=2)

        remove_button = ctk.CTkButton(item_frame, text="X", width=30, fg_color="red", hover_color="darkred",
                                      command=lambda f=item_frame, entries=(name_entry, size_entry, qty_entry, image_path_var): self.remove_item_row(f, entries))
        remove_button.grid(row=0, column=4, padx=2, pady=2)

        self.item_entries.append((name_entry, size_entry, qty_entry, image_path_var, item_frame))
        # Mover el botón de añadir hacia abajo después de añadir la nueva fila
        self.add_item_button.grid(row=len(self.item_entries) + 1, column=0, columnspan=2, pady=(10, 0), sticky="ew")

    def remove_item_row(self, frame_to_remove, entries_to_remove):
        # Eliminar de la lista interna
        self.item_entries = [item for item in self.item_entries if item[4] != frame_to_remove]
        # Destruir el marco y sus widgets
        frame_to_remove.destroy()
        # Ajustar la cuadrícula para los elementos restantes
        for i, (_, _, _, _, f) in enumerate(self.item_entries):
            f.grid(row=i + 1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        # Mover el botón de añadir hacia abajo después de eliminar una fila
        self.add_item_button.grid(row=len(self.item_entries) + 1, column=0, columnspan=2, pady=(10, 0), sticky="ew")

    def select_image_path(self, image_path_var):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen de Producto",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            image_path_var.set(file_path)
            self.status_label.configure(text=f"Imagen seleccionada: {os.path.basename(file_path)}")

    def get_form_data(self):
        numero_pedido = self.entry_pedido.get().strip()
        fecha_venta = self.entry_fecha.get().strip()
        comprador = self.entry_comprador.get().strip()
        precio_total = self.entry_precio.get().strip()

        articulos_vendidos = []
        for name_entry, size_entry, qty_entry, image_path_var, _ in self.item_entries:
            name = name_entry.get().strip()
            size = size_entry.get().strip()
            qty_str = qty_entry.get().strip()
            image_path = image_path_var.get().strip()

            if not name: # Saltar filas de artículos vacías
                continue

            try:
                cantidad = int(qty_str) if qty_str else 1
            except ValueError:
                messagebox.showerror("Error de Entrada", f"Cantidad inválida para '{name}'. Debe ser un número.")
                return None, None, None, None, None # Devolver None para indicar error

            articulos_vendidos.append((name, size, cantidad, image_path if image_path else None))

        if not numero_pedido or not fecha_venta or not comprador or not precio_total or not articulos_vendidos:
            messagebox.showwarning("Faltan Datos", "Por favor, completa todos los campos obligatorios y añade al menos un artículo.")
            return None, None, None, None, None

        return numero_pedido, fecha_venta, comprador, articulos_vendidos, precio_total

    def generate_ticket_action(self):
        self.status_label.configure(text="Generando ticket...")
        numero_pedido, fecha_venta, comprador, articulos_vendidos, precio_total = self.get_form_data()

        if numero_pedido and fecha_venta and comprador and articulos_vendidos and precio_total:
            try:
                file_name = f"Ticket_{numero_pedido}_{comprador.replace(' ', '_')}.pdf"
                pdf_path = generar_ticket_venta_una_pagina(
                    nombre_archivo=file_name,
                    logo_path=LOGO_FILE_PATH,
                    numero_pedido_vinted=numero_pedido,
                    fecha_venta=fecha_venta,
                    comprador=comprador,
                    articulos_vendidos=articulos_vendidos,
                    precio_total=precio_total
                )
                if pdf_path:
                    self.last_generated_pdf_path = pdf_path
                    self.status_label.configure(text=f"Ticket generado: {os.path.basename(pdf_path)}")
                    messagebox.showinfo("Éxito", f"Ticket PDF generado con éxito en:\n{pdf_path}")
                else:
                    self.status_label.configure(text="Error al generar ticket.")
                    messagebox.showerror("Error", "No se pudo generar el ticket PDF. Revisa la consola para más detalles.")
            except Exception as e:
                self.status_label.configure(text=f"Error inesperado: {e}")
                messagebox.showerror("Error Inesperado", f"Ocurrió un error al generar el ticket: {e}")
        else:
            self.status_label.configure(text="Generación cancelada. Faltan datos.")

    def open_email_dialog(self):
        if not self.last_generated_pdf_path or not os.path.exists(self.last_generated_pdf_path):
            messagebox.showwarning("No hay Ticket", "Primero debes generar un ticket antes de enviarlo por email.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Enviar Ticket por Email")
        dialog.geometry("400x250")
        dialog.transient(self) # Hacer que el diálogo aparezca encima de la ventana principal
        dialog.grab_set() # Deshabilitar la interacción con la ventana principal hasta que se cierre el diálogo

        dialog.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(dialog, text="Email del Destinatario:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        email_entry = ctk.CTkEntry(dialog, placeholder_text="ejemplo@dominio.com")
        email_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(dialog, text="Remitente:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(dialog, text=SENDER_EMAIL, font=ctk.CTkFont(weight="bold")).grid(row=1, column=1, padx=10, pady=5, sticky="w")

        attach_checkbox = ctk.CTkCheckBox(dialog, text="Adjuntar PDF original", variable=self.attach_pdf_original)
        attach_checkbox.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        send_button = ctk.CTkButton(dialog, text="Enviar Email",
                                    command=lambda: self.send_email_action(email_entry.get(), dialog))
        send_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    def send_email_action(self, recipient_email, dialog):
        if not recipient_email or "@" not in recipient_email:
            messagebox.showerror("Error de Email", "Por favor, introduce una dirección de email válida.")
            return

        numero_pedido = self.entry_pedido.get().strip()
        comprador = self.entry_comprador.get().strip()

        if not numero_pedido or not comprador:
            messagebox.showwarning("Datos Faltantes", "Necesitas el número de pedido y el nombre del comprador para el email.")
            return

        self.status_label.configure(text=f"Enviando email a {recipient_email}...")
        dialog.destroy() # Cerrar el diálogo de email

        # Ejecutar el envío de email en un hilo separado para evitar que la GUI se congele
        threading.Thread(target=self._send_email_threaded, args=(recipient_email, numero_pedido, comprador)).start()

    def _send_email_threaded(self, recipient_email, numero_pedido, comprador):
        try:
            enviar_ticket_por_correo(
                destinatario_email=recipient_email,
                pdf_path=self.last_generated_pdf_path,
                numero_pedido=numero_pedido,
                comprador=comprador,
                adjuntar_pdf_original_param=self.attach_pdf_original.get()
            )
            self.after(0, lambda: self.status_label.configure(text=f"Email enviado a {recipient_email} exitosamente."))
            self.after(0, lambda: messagebox.showinfo("Éxito de Email", f"El ticket se ha enviado a {recipient_email}."))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"Error al enviar email: {e}"))
            self.after(0, lambda: messagebox.showerror("Error de Email", f"Ocurrió un error al enviar el email: {e}"))


    def clear_form(self):
        self.entry_pedido.delete(0, ctk.END)
        self.entry_fecha.delete(0, ctk.END)
        self.entry_fecha.insert(0, datetime.date.today().strftime("%d/%m/%Y"))
        self.entry_comprador.delete(0, ctk.END)
        self.entry_precio.delete(0, ctk.END)

        # Limpiar y restablecer las entradas de artículos
        for _, _, _, _, frame in self.item_entries:
            frame.destroy()
        self.item_entries = []
        self.add_item_row() # Añadir de nuevo una fila de artículo vacía

        self.last_generated_pdf_path = None
        self.status_label.configure(text="Formulario limpiado. Listo para un nuevo ticket.")

# --- CLASE DE LA VENTANA DE INICIO DE SESIÓN ---
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cast_Sneakers - Iniciar Sesión")
        self.geometry("400x250")
        self.resizable(False, False)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.login_successful = False
        self.active_key_used = None # Nuevo: para almacenar la clave validada

        self.login_frame = ctk.CTkFrame(self, corner_radius=10)
        self.login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.login_frame.grid_columnconfigure(0, weight=1)
        self.login_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.login_frame, text="Acceso a la Aplicación", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 20))

        ctk.CTkLabel(self.login_frame, text="Clave:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.key_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Introduce tu clave", show="*")
        self.key_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.login_button = ctk.CTkButton(self.login_frame, text="Iniciar Sesión", command=self.attempt_login)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=20, sticky="ew", padx=10)

        self.status_label = ctk.CTkLabel(self.login_frame, text="", text_color="red")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=(0, 10))

    def attempt_login(self):
        entered_key = self.key_entry.get().strip()
        if validate_key(entered_key): # Ahora validate_key consulta al backend
            self.login_successful = True
            self.active_key_used = entered_key # Guardar la clave que funcionó
            self.destroy() # Cierra la ventana de login
        else:
            self.status_label.configure(text="Clave inválida o caducada.")
            self.key_entry.delete(0, ctk.END) # Limpia el campo de la clave

# --- Bloque principal de ejecución de la aplicación GUI ---
if __name__ == "__main__":
    # Verificar la existencia de archivos necesarios antes de ejecutar la app
    if not os.path.exists(LOGO_FILE_PATH):
        messagebox.showerror("Error de Archivo", f"El archivo de logo no se encuentra en: {LOGO_FILE_PATH}\nAsegúrate de que 'image.png' esté en la carpeta 'Archivos necesarios'.")
    elif not os.path.exists(os.path.join(ASSETS_DIR, 'Roboto-Regular.ttf')):
        messagebox.showerror("Error de Fuentes", f"Las fuentes 'Roboto' no se encuentran en: {ASSETS_DIR}\nAsegúrate de que los archivos .ttf estén en la carpeta 'Archivos necesarios'.")
    else:
        # Primero, intenta iniciar la aplicación de login
        login_app = LoginWindow()
        login_app.mainloop()

        # Si el login fue exitoso, entonces inicia la aplicación principal
        if login_app.login_successful:
            main_app = TicketGeneratorApp(login_app.active_key_used) # Nuevo: Pasamos la clave activa
            main_app.mainloop()
        else:
            print("Inicio de sesión cancelado o fallido. La aplicación no se iniciará.")
