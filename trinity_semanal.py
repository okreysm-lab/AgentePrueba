import asyncio
import os
import requests
import base64
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
# LEER CORREOS ÚLTIMO 7 DÍAS
# ===============================

def leer_correos_7_dias():
    print("📈 Recopilando actividad de la última semana...")
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build("gmail", "v1", credentials=creds)

    # Filtro: Últimos 7 días
    query = "newer_than:7d -category:promotions -category:social"
    
    results = service.users().messages().list(
        userId="me",
        maxResults=100, 
        q=query
    ).execute()

    mensajes = results.get("messages", [])
    print(f"   Analizando {len(mensajes)} correos recibidos...")

    datos_semanales = []
    for msg in mensajes:
        m = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
        datos_semanales.append(f"De: {headers.get('From')} | Asunto: {headers.get('Subject')} | Fecha: {headers.get('Date')}")

    return datos_semanales

# ===============================
# GROQ: REFLEXIÓN SEMANAL
# ===============================

def generar_reflexion_semanal(correos):
    if not correos:
        return "Hola Yerko, Trinity aquí. No he detectado actividad relevante en los últimos 7 días. ¡Parece que ha sido una semana tranquila!"

    contexto = "\n".join(correos)
    
    # Cargar memoria estratégica si existe para dar más peso al rol de Innovación
    memoria_contexto = ""
    if os.path.exists("trinity_context.json"):
        try:
            with open("trinity_context.json", "r", encoding="utf-8") as f:
                memoria_contexto = f.read()
        except: pass

    prompt = f"""
Eres Trinity, Advisor Senior de Innovación de Yerko.
Hoy es {datetime.now().strftime('%A %d de %B de %Y')}.

TU MISIÓN: Entregar un balance estratégico profundo de la última semana. 
Imagina que Yerko está en un viaje largo y quiere una reflexión seria, conectada y narrativa sobre su desempeño y el de su equipo.

REGLAS:
1. NARRATIVA EXTENSA: No seas breve. Explica las conexiones entre los correos, los proyectos y los objetivos estratégicos de 2026.
2. Identifica los temas que dominaron la semana y por qué son importantes para el futuro.
3. Menciona hitos, pero también riesgos sutiles que detectes en la comunicación.
4. Tono: Inspiracional, ejecutivo y profundo. Saludo: "Hola Yerko".

MEMORIA DE PROYECTOS:
{memoria_contexto}

RESUMEN DE CORREOS ÚLTIMA SEMANA:
{contexto}

FORMATO (Podcast Estratégico):
Hola Yerko, aquí tu balance semanal rodante.

📊 ANÁLISIS DEL PANORAMA SEMANAL:
[Narrativa extensa sobre la carga, el enfoque y la dinámica de la semana]

🏆 VICTORIAS Y AVANCES:
- [Logro 1 con explicación de impacto]
- [Logro 2 con explicación de impacto]

⚠️ MAPA DE RIESGOS Y FOCO:
- [Pendiente crítico o riesgo detectado]
- [Oportunidad de innovación no aprovechada]

🎯 VISIÓN DE ADVISOR:
[Consejo estratégico profundo para su rol de líder]
"""

    client = Groq(api_key=GROQ_API_KEY)
    
    print("\n--- TRINITY EVALUANDO TU SEMANA...\n(Visión 360°) ---\n")
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        max_tokens=3000
    )
    
    return completion.choices[0].message.content

# ===============================
# TELEGRAM: TEXTO Y VOZ
# ===============================

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje[:4000]}, timeout=10)

def generar_y_enviar_audio(texto):
    import re
    archivo_audio = "trinity_semanal_audio.mp3"
    texto_voz = re.sub(r'[🚨ℹ️✅❌📧📋🔴🟡🟢🔵📊🏆⚠️🎯]', '', texto)
    
    async def _generar():
        import edge_tts
        voz = "es-CL-CatalinaNeural"
        comunicar = edge_tts.Communicate(texto_voz, voz)
        await comunicar.save(archivo_audio)

    try:
        asyncio.run(_generar())
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
        with open(archivo_audio, "rb") as audio:
            requests.post(url, data={
                "chat_id": CHAT_ID,
                "title": "Trinity Semanal - Reflexión Estratégica",
                "performer": "Trinity"
            }, files={"audio": audio}, timeout=60)
        os.remove(archivo_audio)
    except Exception as e:
        print(f"⚠️ Audio error: {e}")

# ===============================
# MAIN
# ===============================

def main():
    print("📈 Trinity Semanal - Tu Balance Matutino")
    print("=" * 50)
    
    try:
        correos = leer_correos_7_dias()
        reflexion = generar_reflexion_semanal(correos)
        
        print("\n" + "=" * 50)
        print(reflexion)
        print("=" * 50)
        
        enviar_telegram(reflexion)
        generar_y_enviar_audio(reflexion)
        print("\n✅ Balance enviado a Telegram")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
