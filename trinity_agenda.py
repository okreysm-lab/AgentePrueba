import asyncio
import os
import requests
from datetime import datetime, timezone, timedelta
from groq import Groq
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ===============================
# CONFIG
# ===============================

import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = "8727442796"

# Scopes necesarios: Gmail + Calendar
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly"
]

TOKEN_FILE = "token_agenda.json"
CREDENTIALS_FILE = "credentials.json"


# ===============================
# AUTENTICACIÓN GOOGLE
# ===============================

def autenticar_google():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


# ===============================
# LEER EVENTOS DEL DÍA
# ===============================

def leer_agenda_hoy(creds):
    print("📅 Leyendo agenda del día...")
    service = build("calendar", "v3", credentials=creds)

    # Rango: HOY
    hoy = datetime.now().date()
    inicio = datetime(hoy.year, hoy.month, hoy.day, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    fin    = datetime(hoy.year, hoy.month, hoy.day, 23, 59, 59, tzinfo=timezone.utc).isoformat()

    eventos_result = service.events().list(
        calendarId="primary",
        timeMin=inicio,
        timeMax=fin,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    eventos = eventos_result.get("items", [])
    print(f"   Encontrados {len(eventos)} eventos hoy")

    if not eventos:
        return []

    agenda = []
    for e in eventos:
        start = e.get("start", {})
        hora = start.get("dateTime", start.get("date", "Sin hora"))
        # Limpiar la hora UTC a formato legible
        if "T" in hora:
            hora = hora[11:16]  # Extraer HH:MM
        titulo = e.get("summary", "Sin título")
        descripcion = e.get("description", "")[:300] if e.get("description") else ""
        asistentes = [a.get("email", "") for a in e.get("attendees", [])][:5]

        agenda.append({
            "hora": hora,
            "titulo": titulo,
            "descripcion": descripcion,
            "asistentes": asistentes
        })

    return agenda


# ===============================
# GROQ: BRIEFING DE AGENDA
# ===============================

def generar_briefing_agenda(agenda):
    # Cargar memoria estratégica si existe
    memoria_contexto = ""
    if os.path.exists("trinity_context.json"):
        try:
            with open("trinity_context.json", "r", encoding="utf-8") as f:
                memoria_contexto = f.read()
        except: pass

    if not agenda:
        return "Hola Yerko, Trinity reportando. Hoy tienes la agenda despejada. ¡Buen día para avanzar en proyectos de innovación! 🚀"

    fecha_hoy = datetime.now().strftime("%A %d de %B de %Y")
    agenda_texto = ""
    for e in agenda:
        agenda_texto += f"\n- {e['hora']} hrs: {e['titulo']}"
        if e["descripcion"]:
            agenda_texto += f"\n  Descripción: {e['descripcion']}"
        if e["asistentes"]:
            agenda_texto += f"\n  Asistentes: {', '.join(e['asistentes'])}"

    prompt = f"""
Eres Trinity, la asistente ejecutiva inteligente de Yerko. Eres su Advisor Senior de Innovación.
Hoy es {fecha_hoy}.

MEMORIA ESTRATÉGICA 2026 (Contexto de proyectos):
{memoria_contexto}

MISIÓN: Briefing matutino de la agenda del día.

REGLAS DE ORO:
1. Usa la MEMORIA para dar contexto histórico a las reuniones (ej: "Recuerda que en enero acordaste X").
2. Identifica HUECOS en la agenda y propone BLOQUES DE TRABAJO PROFUNDO (Deep Work) para temas de innovación (VR, Level Up, Diseño).
3. NARRATIVA EXTENSA: No te limites. Yerko tiene viajes largos y quiere profundidad. Explica el "por qué" de las cosas, conecta puntos entre proyectos y personas.
4. El saludo debe ser simplemente: "Hola Yerko".

FORMATO:
Hazlo como si fuera un PODCAST PERSONALIZADO de alta dirección.
Hola Yerko, aquí tu briefing del día.

📅 HOY {fecha_hoy.upper()}:

[Para cada evento:]
🕐 [HORA] — [TÍTULO]
📌 [Qué es y contexto profundo basado en la memoria]
✅ Puntos clave y estrategia:
  - [punto 1 estratégico]
  - [punto 2 estratégico]
💡 Recomendación de Advisor: [recomendación de alto valor]

---
[Cierre con visión de futuro para el día]

AGENDA DEL DÍA:
{agenda_texto}
"""

    client = Groq(api_key=GROQ_API_KEY)

    print("\n--- TRINITY PREPARANDO BRIEFING...\n(Groq Llama 3.3-70B) ---\n")

    respuesta = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        max_tokens=2000
    )

    return respuesta.choices[0].message.content


# ===============================
# TELEGRAM: TEXTO Y VOZ
# ===============================

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje[:4000]}
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ Briefing enviado a Telegram")
    except Exception as e:
        print(f"❌ Error Telegram: {e}")


def generar_y_enviar_audio(texto):
    import re
    archivo_audio = "trinity_agenda_audio.mp3"
    texto_voz = re.sub(r'[🚨ℹ️✅❌📧📋🔴🟡🟢🔵📅🕐📌💡🎯⭐*#]', '', texto)
    # Sin límite de 1500 caracteres para permitir audios largos según pedido del usuario.

    async def _generar():
        import edge_tts
        voz = "es-CL-CatalinaNeural"
        comunicar = edge_tts.Communicate(texto_voz, voz)
        await comunicar.save(archivo_audio)

    try:
        asyncio.run(_generar())
        print("🎙️ Audio generado")

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
        with open(archivo_audio, "rb") as audio:
            requests.post(url, data={
                "chat_id": CHAT_ID,
                "title": "Trinity Agenda - Briefing Diario",
                "performer": "Trinity"
            }, files={"audio": audio}, timeout=60)
        print("🎧 Audio enviado a Telegram")
        os.remove(archivo_audio)
    except Exception as e:
        print(f"⚠️ No se pudo generar audio: {e}")


# ===============================
# MAIN
# ===============================

def main():
    print("🗓️  Trinity Agenda - Briefing del Día")
    print("=" * 50)

    creds = autenticar_google()
    agenda = leer_agenda_hoy(creds)

    briefing = generar_briefing_agenda(agenda)

    print("\n" + "=" * 50)
    print(briefing)
    print("=" * 50)

    enviar_telegram(briefing)

    print("\n🎙️ Generando nota de voz...")
    generar_y_enviar_audio(briefing)

    print("\n✅ Briefing completado")


if __name__ == "__main__":
    main()
