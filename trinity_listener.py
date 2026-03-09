import os
import subprocess
import threading
from dotenv import load_dotenv

# Dependencia necesaria:
# pip install python-telegram-bot
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===============================
# CONFIG
# ===============================
load_dotenv()
TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = int("8727442796")  # Tu ID de Telegram validado (tiene que ser número para comprobarlo)

def ejecutar_script(script_name, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ejecuta un script de Python en segundo plano y avisa al usuario.
    """
    def correr():
        try:
            # Mandamos un mensaje de espera
            # No podemos usar await aqui directamente porque es un thread, pero no importa mucho,
            # el script llamado mandará sus propios mensajes de Telegram.
            print(f"📡 Instrucción recibida: ejecutando {script_name}...")
            # Llamamos al subproceso bloqueante (hasta que acabe)
            subprocess.run(["python", script_name], check=True)
            print(f"✅ {script_name} completado exitosamente.")
        except Exception as e:
            print(f"❌ Error ejecutando {script_name}: {e}")

    # Lanzamos el proceso en un Hilo separado para NO BLOQUEAR el bot de Telegram
    hilo = threading.Thread(target=correr)
    hilo.start()


# ===============================
# HANDLERS DE COMANDOS
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start para iniciar el bot."""
    if update.message.chat_id != CHAT_ID: return # Solo te responde a ti
    
    msg = (
        "👋 ¡Hola Yerko! Soy Trinity, modo interactivo activado.\\n\\n"
        "Puedo ejecutar tus rutinas si me lo pides. Envía los comandos:\\n"
        "👉 /agenda - Prepara la agenda de hoy\\n"
        "👉 /correo - Haz un barrido de tu bandeja de entrada\\n"
        "👉 /resumen - Ejecutar el resumen de proyectos semanales\\n"
        "👉 /radar - Buscar novedades de IA en internet\\n"
        "👉 /curiosidades - Enviar alguna curiosidad al azar"
    )
    await update.message.reply_text(msg)

async def cmd_agenda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != CHAT_ID: return
    await update.message.reply_text("🗓️ Entendido Yerko. Revisando tu agenda de Google... (te llegará el mensaje pronto)")
    ejecutar_script("trinity_agenda.py", update, context)

async def cmd_correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != CHAT_ID: return
    await update.message.reply_text("📧 A la orden. Escaneando prioridad de correos nuevos en Gmail...")
    ejecutar_script("trinity_correo.py", update, context)

async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != CHAT_ID: return
    await update.message.reply_text("📊 Iniciando análisis profundo de proyectos semanales (Team)...")
    ejecutar_script("trinity_planner.py", update, context)

async def cmd_radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != CHAT_ID: return
    await update.message.reply_text("📡 Inicializando rastreador de IA y tecnología mundial...")
    ejecutar_script("trinity_radar.py", update, context)

async def cmd_curiosidades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != CHAT_ID: return
    await update.message.reply_text("🧠 Buscando algo interesante para ti...")
    ejecutar_script("trinity_curiosidades.py", update, context)

async def mensaje_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Si escribes texto normal en vez de un comando con / slash"""
    if update.message.chat_id != CHAT_ID: return
    texto = update.message.text.lower()
    
    if "correo" in texto or "email" in texto:
        await cmd_correo(update, context)
    elif "agenda" in texto or "reuniones" in texto:
        await cmd_agenda(update, context)
    elif "resumen" in texto or "proyectos" in texto:
        await cmd_resumen(update, context)
    elif "radar" in texto or "ia" in texto or "noticia" in texto:
        await cmd_radar(update, context)
    elif "curiosidad" in texto or "dato" in texto:
        await cmd_curiosidades(update, context)
    else:
        await update.message.reply_text("🤖 Trinity escuchando. No reconozco de qué tarea hablas. Usa /start para ver las opciones disponibles.")

def main():
    print("🤖 Iniciando Trinity Listener (Modo Interactivo de Telegam)...")
    
    # Preparamos la App con tu Token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Registramos los comandos del bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("agenda", cmd_agenda))
    application.add_handler(CommandHandler("correo", cmd_correo))
    application.add_handler(CommandHandler("resumen", cmd_resumen))
    application.add_handler(CommandHandler("radar", cmd_radar))
    application.add_handler(CommandHandler("curiosidades", cmd_curiosidades))

    # Y registramos si escribes texto normal sin slash (/)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_texto))

    print("🟢 Escuchando mensajes (Presiona Ctrl+C para detener)...")
    # Inicia el "Long Polling" continuo
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
