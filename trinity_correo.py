import asyncio
import os
import base64
import requests
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ===============================
# CONFIG
# ===============================

from groq import Groq

import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = "8727442796"

MAX_CORREOS = 30


# ===============================
# TELEGRAM
# ===============================

def enviar_telegram(mensaje):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": mensaje[:4000]
    }

    try:
        requests.post(url, data=data, timeout=10)
        print("Mensaje enviado a Telegram")
    except:
        print("No se pudo enviar a Telegram")


def generar_y_enviar_audio(texto):
    """Genera MP3 con edge-tts (voz de Microsoft) y lo manda a Telegram como nota de voz."""

    archivo_audio = "trinity_audio.mp3"

    # Limpiar emojis y texto para que suene natural en voz
    import re
    texto_voz = re.sub(r'[🚨ℹ️✅❌📧📋🔴🟡🟢🔵🆕👤📌➡️✉️]', '', texto)
    texto_voz = texto_voz.replace("querido Yerko", "Yerko") # por si acaso
    texto_voz = texto_voz.replace("Hola Yerko", "Yerko")
    texto_voz = texto_voz[:1500] 

    async def _generar():
        import edge_tts
        voz = "es-CL-CatalinaNeural"  # Voz chilena femenina de Microsoft
        comunicar = edge_tts.Communicate(texto_voz, voz)
        await comunicar.save(archivo_audio)

    try:
        asyncio.run(_generar())
        print("🎙️ Audio generado con voz chilena")

        # Enviar como nota de voz a Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
        with open(archivo_audio, "rb") as audio:
            files = {"voice": audio}
            data = {"chat_id": CHAT_ID}
            requests.post(url, data=data, files=files, timeout=30)
        print("🎧 Nota de voz enviada a Telegram")

        os.remove(archivo_audio)
    except Exception as e:
        print(f"⚠️ No se pudo generar el audio: {e}")




# ===============================
# LIMPIAR TEXTO
# ===============================

def limpiar_texto(texto):

    if not texto:
        return ""

    texto = texto.replace("\n", " ")
    texto = texto.replace("\r", " ")

    texto = texto.strip()

    return texto[:400]


# ===============================
# LEER CORREOS
# ===============================

def leer_correos():

    creds = Credentials.from_authorized_user_file("token.json")

    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me",
        maxResults=100, # Reducido para evitar rate limit de Groq
        q="newer_than:4d"
    ).execute()

    mensajes = results.get("messages", [])

    correos = []

    for msg in mensajes:

        m = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject"]
        ).execute()

        headers = m["payload"]["headers"]

        subject = ""
        sender = ""

        for h in headers:

            if h["name"] == "Subject":
                subject = h["value"]

            if h["name"] == "From":
                sender = h["value"]

        snippet = limpiar_texto(m.get("snippet", ""))

        correos.append(
            f"""
ID_CORREO: {msg['id']}
De: {sender}
Asunto: {subject}
Fragmento: {snippet}
"""
        )

    return correos


# ===============================
# GROQ CLOUD IA
# ===============================

def analizar_con_trinity(correos):

    contexto = "\n".join(correos)

    prompt = f"""
Eres Trinity, la asistente ejecutiva implacable y resolutiva de Yerko. Eres un LLM de 70 Billones de parámetros y eres sumamente inteligente.

REGLAS ESTRICTAS PARA TU RESPUESTA:
- NO incluyas textos como "ID_CORREO" ni códigos raros en tu respuesta. Yerko es un humano, háblale como humano.
- Sigue ESTRICTAMENTE el formato de abajo, destacando siempre QUIÉN envía el correo.
- Ignora cualquier correo que sea newsletter, propaganda, spam o "gracias".

FORMATO OBLIGATORIO DE RESPUESTA:
Hola Yerko, Trinity reportando desde la nube.

🚨 URGENTE O REQUIERE ACCIÓN:
- [Nombre del Remitente]: [Explicación clara y conversacional de qué trata el correo y qué debes hacer]

ℹ️ PARA TU INFORMACIÓN (Trabajo):
- [Nombre del Remitente]: [Explicación resumida de la información útil que llegó]

✉️ BORRADORES DE RESPUESTA SUGERIDOS:
[Para cada correo URGENTE, propón un borrador de respuesta breve y profesional listo para copy-paste en español. Usa el formato:
PARA: [Nombre remitente]
ASUNTO: Re: [Asunto original]
MENSAJE: [Borrador de respuesta]]

AQUÍ ESTÁN LOS CORREOS (Saca la información de aquí, analízala y redáctala según el formato exigido):
{contexto}
"""

    if not GROQ_API_KEY.startswith("gsk_"):
        return "⚠️ Error: API Key de Groq inválida."

    try:
        print("\n--- TRINITY PENSANDO EN LA NUBE...\n(Esto tomará menos de 3 segundos) ---\n")
        
        client = Groq(api_key=GROQ_API_KEY)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1024
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"Error conectando con Groq: {e}"


# ===============================
# MAIN
# ===============================

def main():

    print("Leyendo correos...")
    correos = leer_correos()

    print("Analizando con Trinity...")
    resumen = analizar_con_trinity(correos)

    print(resumen)

    # Enviar texto a Telegram
    enviar_telegram(resumen)

    # Generar y enviar nota de voz
    print("\n🎙️ Generando nota de voz...")
    generar_y_enviar_audio(resumen)


if __name__ == "__main__":
    main()