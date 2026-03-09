import asyncio
import os
import requests
import re
import json
from datetime import datetime
from groq import Groq

# ===============================
# CONFIG
# ===============================

import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = "8727442796"

# ===============================
# GROQ: GENERAR CURIOSIDAD INCREÍBLE
# ===============================

def generar_curiosidad():
    print("🧠 Trinity buscando algo realmente increíble para ti...")
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = """
Eres "Trinity Wow", una versión de la IA enfocada en descubrir y explicar hechos absolutamente fascinantes e increíbles.
Tu objetivo es dejar a Yerko con la boca abierta mientras trota.

TEMAS POSIBLES:
- Neurociencia aplicada (cómo funciona el cerebro ante el ejercicio).
- Tecnología de frontera (computación cuántica, biotecnología).
- Misterios del universo o la física.
- Curiosidades de la historia de la innovación.

TAREAS:
1. Elige UN tema que sea verdaderamente sorprendente hoy.
2. Crea un guion de audio EXTENSO (unas 500-700 palabras) que se sienta como un mini-documental sonoro.
3. El tono debe ser épico, curioso y apasionado.
4. Saludo: "Hola Yerko, prepárate para esto..."

RESPONDE SOLO CON JSON:
{
  "titulo": "Título del tema increíble",
  "reporte_texto": "Resumen en Markdown para Telegram...",
  "resumen_voz": "Guion completo para ser leído por TTS..."
}
"""

    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.8, # Más creativo para curiosidades
        response_format={"type": "json_object"}
    )
    
    return json.loads(completion.choices[0].message.content)

# ===============================
# ENTREGAS
# ===============================

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}, timeout=10)

async def generar_y_enviar_audio(texto_voz):
    archivo_audio = "trinity_wow_audio.mp3"
    import edge_tts
    
    # Limpiar de caracteres especiales para TTS
    texto_voz = re.sub(r'[🚨ℹ️✅❌📧📋🔴🟡🟢🔵📊🏆⚠️🎯🎥🧠📅*#]', '', texto_voz)
    
    voz = "es-CL-CatalinaNeural"
    comunicar = edge_tts.Communicate(texto_voz, voz)
    print("🔊 Generando audio (Epic Science)...")
    await comunicar.save(archivo_audio)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
    with open(archivo_audio, "rb") as audio:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "title": "Trinity Wow - Curiosidades",
            "performer": "Trinity"
        }, files={"audio": audio}, timeout=60)
    os.remove(archivo_audio)

# ===============================
# MAIN
# ===============================

def main():
    print("✨ Iniciando Trinity Wow - Curiosidades")
    print("=" * 50)
    
    data = generar_curiosidad()
    
    print(f"📩 Enviando '{data['titulo']}' a Telegram...")
    enviar_telegram(f"✨ *TRINITY WOW: {data['titulo']}*\n\n{data['reporte_texto']}")
    
    print("🎙️ Generando Podcast de Curiosidades...")
    asyncio.run(generar_y_enviar_audio(data["resumen_voz"]))
    
    print("\n✅ Curiosidad enviada.")

if __name__ == "__main__":
    main()
