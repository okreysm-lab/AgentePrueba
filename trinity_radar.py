import asyncio
import os
import requests
import feedparser
import yt_dlp
import re
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

CHANNELS_YT = [
    "https://www.youtube.com/@AIExplained/videos",
    "https://www.youtube.com/@TwoMinutePapers/videos",
    "https://www.youtube.com/@DotCSVLab/videos",
    "https://www.youtube.com/@Platzi/videos",
    "https://www.youtube.com/@rodrigolivaresr/videos",
    "https://www.youtube.com/@joaquinbarberaaledo/videos",
    "https://www.youtube.com/@victorroblesweb/videos",
    "https://www.youtube.com/@FaztTech/videos",
    "https://www.youtube.com/@alejavirivera/videos"
]

# ===============================
# EXTRACCIÓN DE DATOS
# ===============================

def get_latest_news():
    print("📰 Buscando noticias de IA en el radar...")
    noticias_raw = []
    # (Opcional: Volver a agregar RSS si Yerko lo pide, por ahora solo YT para español)
    return noticias_raw

def get_latest_videos():
    print("🎥 Monitoreando canales de YouTube estratégicos...")
    videos_raw = []
    ydl_opts = {"quiet": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for channel in CHANNELS_YT:
            try:
                info = ydl.extract_info(channel, download=False)
                for video in info["entries"][:2]:
                    videos_raw.append({
                        "titulo": video["title"],
                        "url": f"https://youtube.com/watch?v={video['id']}"
                    })
            except: pass
    return videos_raw

# ===============================
# GROQ: ANÁLISIS Y PODCAST SCRIPT
# ===============================

def analizar_y_crear_radar(noticias, videos):
    print("🧠 Trinity analizando tendencias... (Llama 3.3-70B)")
    client = Groq(api_key=GROQ_API_KEY)
    
    # Cargar contexto Yerko si existe
    contexto_yerko = ""
    if os.path.exists("trinity_context.json"):
        with open("trinity_context.json", "r", encoding="utf-8") as f:
            contexto_yerko = f.read()

    # Guion de podcast más extenso según solicitud del usuario
    prompt = f"""
Eres Trinity, Advisor de Innovación de Yerko.
Tu misión es seleccionar lo mejor de la IA de hoy y presentarlo de forma potente en un formato de podcast corto para trotar.

CONTEXTO DE YERKO (Para personalización):
{contexto_yerko[:1000]}

NOTICIAS RAW:
{json.dumps(noticias, ensure_ascii=False)}

VIDEOS RAW:
{json.dumps(videos, ensure_ascii=False)}

TAREAS:
1. Selecciona las noticias y videos más potentes. Prioriza los canales en español si tienen contenido fresco.
2. Crea un GUION DE PODCAST EXTENSO Y DETALLADO (alrededor de 600-800 palabras) para que tú lo leas.
   - Debe ser conversacional, profundo, vibrante.
   - Explica las implicaciones técnicas y de negocio. 
   - Saludo: "Hola Yerko".

RESPONDE SOLO CON JSON:
{{
  "reporte_texto": "Texto Markdown...",
  "resumen_voz": "Guion extenso para TTS..."
}}
"""

    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    return json.loads(completion.choices[0].message.content)

# ===============================
# ENTREGAS (TELEGRAM Y TTS)
# ===============================

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}, timeout=10)

async def generar_y_enviar_audio(texto_voz):
    archivo_audio = "trinity_radar_audio.mp3"
    import edge_tts
    
    # Limpiar texto para TTS
    texto_voz = re.sub(r'[🚨ℹ️✅❌📧📋🔴🟡🟢🔵📊🏆⚠️🎯🎥🧠📅*#]', '', texto_voz)
    
    voz = "es-CL-CatalinaNeural"
    comunicar = edge_tts.Communicate(texto_voz, voz)
    await comunicar.save(archivo_audio)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
    with open(archivo_audio, "rb") as audio:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "title": "Trinity Radar IA - Noticias",
            "performer": "Trinity"
        }, files={"audio": audio}, timeout=60)
    os.remove(archivo_audio)

# ===============================
# MAIN
# ===============================

def main():
    print("📡 Iniciando Trinity Radar IA")
    print("=" * 50)
    
    noticias = get_latest_news()
    videos = get_latest_videos()
    
    radar = analizar_y_crear_radar(noticias, videos)
    
    print("\n📩 Enviando Radar a Telegram...")
    enviar_telegram(radar["reporte_texto"])
    
    print("🎙️ Generando Mini-Podcast de Catalina...")
    asyncio.run(generar_y_enviar_audio(radar["resumen_voz"] if "resumen_voz" in radar else radar["podcast_script"]))
    
    print("\n✅ Radar completado.")

if __name__ == "__main__":
    import json
    main()
