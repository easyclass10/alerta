import smtplib
from email.mime.text import MIMEText
import yfinance as yf
import os  # Para leer variables de entorno

# --- Diccionario con precios de compra de las acciones ---
purchases = {
    'VOO.CL': 10.0,    # Ejemplo: precio de compra para NU
    'NVDA.CL': 200.0, # Ejemplo: precio de compra para TSLA
    'META.CL': 300.0  # Ejemplo: precio de compra para MSFT
    #'AMDVASCCO.CL': 
}

# --- Función para obtener el valor del dólar usando yfinance ---
def obtener_tasa_usd_cop():
    ticker = yf.Ticker("COP=X")
    data = ticker.history(period="1d", interval="1m")  # últimos datos del día
    if data.empty:
        raise ValueError("No se pudo obtener la tasa USD/COP")
    tasa_cop_usd = data["Close"].iloc[-1]  # COP por USD
    return 1 / tasa_cop_usd if tasa_cop_usd != 0 else None  # Invertir para USD a COP

# --- Función para obtener el precio actual de una acción ---
def obtener_precio_actual(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    data = ticker.history(period="1d", interval="1m")
    if data.empty:
        raise ValueError(f"No se pudo obtener el precio de {ticker_symbol}")
    return data["Close"].iloc[-1]

# --- Función para calcular el cambio porcentual ---
def calcular_cambio_porcentual(precio_compra, precio_actual):
    if precio_compra == 0:
        return 0.0
    return ((precio_actual - precio_compra) / precio_compra) * 100

# --- Función para enviar el correo ---
def enviar_correo(remitente, clave_app, destinatario, asunto, mensaje):
    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destinatario

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(remitente, clave_app)
        server.send_message(msg)

# --- Script principal ---
if __name__ == "__main__":
    # Cargar secretos desde las variables de entorno
    remitente_email = os.environ.get("SENDER_EMAIL")
    clave_aplicacion = os.environ.get("APP_PASSWORD")
    destinatario_email = os.environ.get("RECIPIENT_EMAIL")
    
    # Validar que se cargaron todos los secretos
    if not all([remitente_email, clave_aplicacion, destinatario_email]):
        print("Error: Faltan variables de entorno (SENDER_EMAIL, APP_PASSWORD, RECIPIENT_EMAIL).")
        exit(1)

    try:
        usd_cop = obtener_tasa_usd_cop()
        if usd_cop is None:
            raise ValueError("Tasa USD/COP inválida.")
        print(f"Tasa actual USD→COP: {usd_cop}")
        
        # Obtener precios actuales y calcular cambios
        cambios = {}
        for ticker, precio_compra in purchases.items():
            precio_actual = obtener_precio_actual(ticker)
            cambio = calcular_cambio_porcentual(precio_compra, precio_actual)
            cambios[ticker] = cambio
        
        # Construir el mensaje de alerta
        mensaje = f"Alerta:\n\nDólar {usd_cop:.2f} COP\n"
        for ticker, cambio in cambios.items():
            signo = '+' if cambio >= 0 else '-'
            mensaje += f"{ticker}: {signo}{abs(cambio):.0f}%\n"
        
        asunto = "Alerta de Acciones y Dólar"
        
        # Enviar el correo siempre
        enviar_correo(remitente_email, clave_aplicacion, destinatario_email, asunto, mensaje)
        print("Correo enviado correctamente.")
        
    except Exception as e:
        print("Error:", e)
        # Opcional: enviar correo de error si se desea
