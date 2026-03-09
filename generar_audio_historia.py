import asyncio
import os
import requests
import re
import edge_tts

# ===============================
# CONFIG
# ===============================

TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = "8727442796"
GUION_FILE = "guion_anual_final.txt"
AUDIO_FILE = "trinity_historia_anual_completa.mp3"

# ===============================
# MOTOR DE AUDIO
# ===============================

async def generar_audio():
    print(f"🎙️ Leyendo guion de {GUION_FILE}...")
    with open(GUION_FILE, "r", encoding="utf-8") as f:
        texto = f.read()

    # Limpiar de caracteres especiales para TTS
    texto = re.sub(r'[🚨ℹ️✅❌📧📋🔴🟡🟢🔵📊🏆⚠️🎯🎥🧠📅*#]', '', texto)
    
    voz = "es-CL-CatalinaNeural"
    comunicar = edge_tts.Communicate(texto, voz)
    
    print("🔊 Generando audio de larga duración (Podcast Yerko 2025-2026)...")
    print("⏳ Esto puede tardar unos minutos debido a la extensión del archivo.")
    await comunicar.save(AUDIO_FILE)
    
    print("📦 Audio generado con éxito. Enviando a Telegram como AUDIO...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
    with open(AUDIO_FILE, "rb") as audio:
        response = requests.post(
            url, 
            data={
                "chat_id": CHAT_ID, 
                "caption": "🎙️ *La Historia de tu Año (Versión Long-Form)*\n\nEste es el podcast de 15 minutos que recorre tu trayectoria desde Marzo 2025. ¡Disfrútalo!",
                "title": "La Odisea de Innovación",
                "performer": "Trinity AI"
            }, 
            files={"audio": audio}, 
            timeout=300 # Timeout alto para archivos grandes
        )
    
    if response.status_code == 200:
        print("✅ Podcast enviado satisfactoriamente.")
    else:
        print(f"❌ Error al enviar: {response.text}")
    
    os.remove(AUDIO_FILE)

if __name__ == "__main__":
    asyncio.run(generar_audio())
