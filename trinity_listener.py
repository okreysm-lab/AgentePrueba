import os
import sys
import subprocess
import threading
import json
from dotenv import load_dotenv

# Dependencias necesarias
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# ===============================
# CONFIG
# ===============================
load_dotenv()
TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = int("8727442796")  
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def ejecutar_script(script_name, argumentos=None):
    """Ejecuta un script de Python en segundo plano"""
    def correr():
        try:
            print(f"📡 Instrucción recibida: ejecutando {script_name}...")
            comando = ["python", script_name]
            if argumentos:
                comando.extend(argumentos)
            subprocess.run(comando, check=True)
            print(f"✅ {script_name} completado.")
        except Exception as e:
            print(f"❌ Error ejecutando {script_name}: {e}")

    hilo = threading.Thread(target=correr)
    hilo.start()


# ===============================
# MOTOR LLM - PROCESAMIENTO
# ===============================
async def pensar_y_actuar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Toma el texto del usuario, lo lanza al LLM para que devuelva un JSON con la intención
    y ejecuta el script correspondiente.
    """
    if update.message.chat_id != CHAT_ID: return
    
    texto_usuario = update.message.text
    
    # Comandos basicos hardcodeados por si acaso
    if texto_usuario.startswith("/"):
        if texto_usuario == "/start":
            await update.message.reply_text("👋 Hola Yerko, soy Trinity Nivel 3. Puedes darme instrucciones en lenguaje natural ahora (Ej: 'Revisa si Paula me mandó un correo ayer sobre Agrosuper').")
        return

    # Mensaje de carga para mejorar la interactividad
    msg_espera = await update.message.reply_text("🧠 Analizando tu petición...")
    
    prompt_sistema = """
Eres Trinity, asistente de lectura personal de Yerko. 
Tu única misión aquí es clasificar comandos. Yerko te va a pedir que leas correos, le des el resumen del día, etc.
Responde ÚNICA Y EXCLUSIVAMENTE con un JSON puro con este formato:
{
  "intencion": "ComandoDetectado",
  "razonamiento": "Por qué elegiste esta intención brevemente",
  "parametros": {}
}

Las ÚNICAS "intenciones" válidas (CommandosDetectados) son:
- RUTINA_CORREO: Si pide un chequeo/barrido GENERAL de spam y VIPs.
- RUTINA_RESUMEN: Si pide el planner/tabla semanal de proyectos (Team).
- RUTINA_AGENDA: Si pide ver la agenda de hoy.
- RUTINA_RADAR: Si pide novedades de tecnologia o IA en general.
- RUTINA_CURIOSIDADES: Si pide una curiosidad.
- LEER_CORREO_ESPECIFICO: **ESTA ES LA MÁS IMPORTANTE**. Úsala si pide información sobre una PERSONA concreta, FECHA específica o PROYECTO puntual.
   -> Si eliges LEER_CORREO_ESPECIFICO, los "parametros" DEBEN incluir "gmail_query" (una query válida de GMails, ej: "from:paula after:2025/10/01") y "descripcion" (el resumen de qué buscar en corto).

Ejemplo 1 de Usuario: "Dime si Paula me respondió ayer"
Debe devolver: {"intencion": "LEER_CORREO_ESPECIFICO", "razonamiento": "Busca un remitente", "parametros": {"gmail_query": "from:paula newer_than:2d", "descripcion": "Correos de Paula en los últimos 2 días"}}

Ejemplo 2 de Usuario: "Muéstrame la agenda"
Debe devolver: {"intencion": "RUTINA_AGENDA", "razonamiento": "Palabra clave agenda", "parametros": {}}
"""
    
    client = Groq(api_key=GROQ_API_KEY)
    try:
        respuesta = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Mensaje de Yerko: '{texto_usuario}'"}
            ],
            model="llama3-8b-8192",
            temperature=0.0
        )
        # Extraer el JSON 
        raw_llm = respuesta.choices[0].message.content
        # Limpiar posibles mardowns
        if "```json" in raw_llm:
            raw_llm = raw_llm.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_llm:
            raw_llm = raw_llm.split("```")[1].strip()
            
        estado = json.loads(raw_llm)
        print(f"\\n🧠 INTENCIÓN DETECTADA: {estado['intencion']} ({estado['razonamiento']})\\n")
        
        # ELABORAR ACCIÓN BASADA EN INTENCIÓN
        intencion = estado["intencion"]
        
        if intencion == "LEER_CORREO_ESPECIFICO":
            query = estado["parametros"].get("gmail_query", "")
            desc = estado["parametros"].get("descripcion", texto_usuario)
            await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=msg_espera.message_id, 
                                          text=f"🔍 Recibido. Buscando correos específicos relacionados a tu petición...")
            ejecutar_script("trinity_correo_dinamico.py", [query, desc])
            
        elif intencion == "RUTINA_CORREO":
            await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=msg_espera.message_id, 
                                          text="📧 Escaneando la bandeja de entrada según prioridad...")
            ejecutar_script("trinity_correo.py")
            
        elif intencion == "RUTINA_AGENDA":
            await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=msg_espera.message_id, 
                                          text="🗓️ Preparando tu agenda de hoy...")
            ejecutar_script("trinity_agenda.py")
            
        elif intencion == "RUTINA_RESUMEN":
            await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=msg_espera.message_id, 
                                          text="📊 Iniciando análisis de la semana, dame un minuto...")
            ejecutar_script("trinity_planner.py")
            
        elif intencion == "RUTINA_RADAR":
            await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=msg_espera.message_id, 
                                          text="📡 Rastreando IA Mundial...")
            ejecutar_script("trinity_radar.py")
            
        elif intencion == "RUTINA_CURIOSIDADES":
            await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=msg_espera.message_id, 
                                          text="🧠 Pensando en algo genial...")
            ejecutar_script("trinity_curiosidades.py")
            
        else:
            await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=msg_espera.message_id, 
                                          text="🤖 Esa me pilló por sorpresa, no tengo un módulo para ejecutar eso.")
            
    except Exception as e:
        print(f"Error procesando LLM en Telegram: {e}")
        await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=msg_espera.message_id, 
                                            text="❌ Oh oh. Tengo jaqueca. Mi conexión con Groq falló o no entendí el formato JSON.")

def main():
    print("🤖 Iniciando Trinity Listener (NIVEL 3 - MODO INTELIGENTE)...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Escuchamos TODOS los textos no-comandos y los pasamos por la IA
    application.add_handler(MessageHandler(filters.TEXT, pensar_y_actuar))

    print("🟢 Escuchando lenguaje natural... (Presiona Ctrl+C para detener)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
