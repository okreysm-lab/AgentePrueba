import asyncio
import os
import requests
import base64
import json
import re
from datetime import datetime, timedelta
from groq import Groq
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ===============================
# CONFIG
# ===============================

import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = "8727442796"
TOKEN_FILE = "token.json"

# ===============================
# ANALIZADOR DE HISTORIA ANUAL
# ===============================

def leer_hitos_anuales():
    print("📜 Buceando en la historia (Marzo 2025 - Marzo 2026)...")
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build("gmail", "v1", credentials=creds)

    # Vamos a leer por trimestres para no saturar y captar la evolución
    trimestres = [
        {"nombre": "Q2 2025", "query": "after:2025/03/01 before:2025/07/01"},
        {"nombre": "Q3 2025", "query": "after:2025/07/01 before:2025/11/01"},
        {"nombre": "Q4 2025", "query": "after:2025/11/01 before:2026/01/01"},
        {"nombre": "Q1 2026", "query": "after:2026/01/01"}
    ]

    historia_raw = {}

    for tri in trimestres:
        print(f"   Analizando {tri['nombre']}...")
        results = service.users().messages().list(
            userId="me", 
            q=f"{tri['query']} (Innovación OR Proyecto OR OT OR Estrategia)",
            maxResults=50
        ).execute()
        
        mensajes = results.get("messages", [])
        hitos_tri = []
        for msg in mensajes:
            m = service.users().messages().get(userId="me", id=msg["id"], format="metadata", metadataHeaders=["Subject", "Date"]).execute()
            headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
            hitos_tri.append(f"{headers.get('Date')}: {headers.get('Subject')}")
        
        historia_raw[tri["nombre"]] = hitos_tri

    return historia_raw

# ===============================
# GROQ: NARRATIVA ÉPICA
# ===============================

def generar_capitulo(client, titulo_cap, contexto_datos, instrucciones_especificas):
    print(f"🎙️ Redactando {titulo_cap}...")
    prompt = f"""
Eres Trinity, la historiadora estratégica de Yerko.
Misión: Escribir el {titulo_cap} del podcast "La Odisea de Innovación".

DATOS DISPONIBLES:
{json.dumps(contexto_datos, indent=2, ensure_ascii=False)}

INSTRUCCIONES:
{instrucciones_especificas}
- Escucha de Yerko: Él quiere un audio largo. Escribe al menos 500-700 palabras SOLO para este capítulo.
- Tono: Narrativo, profundo, Advisor Senior de Innovación.
- No uses código, etiquetas, ni digas "Capítulo X". Solo el texto fluido para ser leído.

RESPONDE UNICAMENTE CON EL TEXTO NARRATIVO DEL CAPÍTULO.
"""
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=2000
    )
    return completion.choices[0].message.content.strip()

def generar_podcast_historia(datos):
    print("🧠 Trinity iniciando producción por capítulos para máxima profundidad...")
    client = Groq(api_key=GROQ_API_KEY)
    
    capitulos = [
        ("INTRODUCCIÓN", datos, "Habla de marzo 2025, el inicio de Yerko en este ciclo, sus expectativas y el clima de innovación. Saludo: 'Hola Yerko, prepárate. Hoy no vamos a correr, vamos a viajar por tu historia...'"),
        ("CAPÍTULO 1: LA SEMILLA", {k: v for k, v in datos.items() if "2025" in k and ("Q2" in k or "Q3" in k)}, "Detalla la evolución de proyectos como Agrosuper y Landes. Conecta nombres y hitos."),
        ("CAPÍTULO 2: EL CRECIMIENTO", {k: v for k, v in datos.items() if "Q4" in k}, "Habla de la consolidación de IACC, Cencosud y el fortalecimiento del equipo (Mayerlin, Andrés, Natalia)."),
        ("CAPÍTULO 3: EL PRESENTE", {k: v for k, v in datos.items() if "2026" in k}, "Analiza el inicio de este año, tu rol con los gestores de proyecto y la visión estratégica actual."),
        ("CONCLUSIÓN", datos, "Reflexión final sobre el camino recorrido y el futuro que se construye desde la innovación.")
    ]
    
    guion_total = []
    for titulo, contexto, instruccion in capitulos:
        texto = generar_capitulo(client, titulo, contexto, instruccion)
        guion_total.append(texto)
        # Pequeña pausa para evitar rate limits
        import time
        time.sleep(2)
    
    return {
        "titulo": "La Odisea de Innovación: Tu Año 2025-2026",
        "reporte_texto": "Tu historia anual ha sido procesada capítulo a capítulo para capturar cada detalle estratégico.",
        "guion_podcast": "\n\n".join(guion_total)
    }

# ===============================
# ENTREGAS
# ===============================

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje[:4000], "parse_mode": "Markdown"}, timeout=10)

async def generar_y_enviar_audio(texto_voz):
    archivo_audio = "trinity_historia_anual.mp3"
    import edge_tts
    
    # Limpiar texto para TTS
    texto_voz = re.sub(r'[🚨ℹ️✅❌📧📋🔴🟡🟢🔵📊🏆⚠️🎯🎥🧠📅*#]', '', texto_voz)
    
    voz = "es-CL-CatalinaNeural"
    # Catalina es ideal para narrativas largas por su calidez
    comunicar = edge_tts.Communicate(texto_voz, voz)
    print("🎙️ Generando audio long-form... (Esto puede tardar unos minutos)")
    await comunicar.save(archivo_audio)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
    with open(archivo_audio, "rb") as audio:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"voice": audio}, timeout=120)
    os.remove(archivo_audio)

# ===============================
# MAIN
# = :=============================

def main():
    print("🎙️ Iniciando Agente de Memoria Anual - La Historia de tu Año")
    print("=" * 60)
    
    try:
        datos = leer_hitos_anuales()
        historia = generar_podcast_historia(datos)
        
        print("\n📩 Enviando Introducción a Telegram...")
        enviar_telegram(f"🎙️ *{historia['titulo']}*\n\n{historia['reporte_texto']}")
        
        # Auditoría de longitud
        print(f"📏 Longitud del guion: {len(historia['guion_podcast'].split())} palabras.")
        with open("debug_guion.txt", "w", encoding="utf-8") as f:
            f.write(historia["guion_podcast"])

        print("🎧 Generando el Gran Podcast Anual (Long-Form)...")
        asyncio.run(generar_y_enviar_audio(historia["guion_podcast"]))
        
        print("\n✅ Historia anual completada. ¡Disfruta el viaje, Yerko!")
        
    except Exception as e:
        print(f"❌ Error en la historia anual: {e}")

if __name__ == "__main__":
    main()
