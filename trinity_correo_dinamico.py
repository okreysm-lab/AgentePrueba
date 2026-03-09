import sys
import base64
import json
import requests
from groq import Groq
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = "8727442796"
TOKEN_FILE = "token.json"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error Telegram: {e}")

def analizar_correo_dinamico(query_gmail, descripcion_usuario):
    """
    Busca correos en Gmail usando el query especifico y usa Groq
    para responder la pregunta exacta del usuario.
    """
    print(f"Buscando en Gmail con query: {query_gmail}")
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build("gmail", "v1", credentials=creds)

    try:
        results = service.users().messages().list(
            userId="me", 
            q=query_gmail,
            maxResults=10  # Solo leemos los ultimos 10 para no saturar 
                           # y dar una respuesta rapida al celular.
        ).execute()
    except Exception as e:
        enviar_telegram(f"❌ Error buscando en Gmail: {e}")
        return

    mensajes = results.get("messages", [])
    if not mensajes:
        enviar_telegram(f"📭 Revisé tu correo, pero no encontré nada reciente que coincida con tu búsqueda sobre: *{descripcion_usuario}*")
        return

    # Extraer contenido de los correos encontrados
    correos_texto = ""
    for msg in mensajes:
        try:
            m = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
            
            cuerpo = ""
            payload = m.get("payload", {})
            partes = payload.get("parts", [payload])
            
            for parte in partes:
                mime = parte.get("mimeType", "")
                if "text/plain" in mime or "text" in mime:
                    data = parte.get("body", {}).get("data", "")
                    if data:
                        try:
                            cuerpo = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                            cuerpo = " ".join(cuerpo.split())[:1000] # Limite razonable por correo
                            break
                        except: pass
            
            if not cuerpo:
                cuerpo = m.get("snippet", "")
            
            correos_texto += f"\\n--- Correo ---\\nDe: {headers.get('From', '')}\\nFecha: {headers.get('Date', '')}\\nAsunto: {headers.get('Subject', '')}\\nMensaje: {cuerpo}\\n"
        except:
            pass

    # Usar Groq para responder al usuario usando esos correos
    prompt = f"""
Eres Trinity, asistente de Yerko Verdugo. 
El usuario (Yerko) te pidió específicamente esto: "{descripcion_usuario}"

He buscado en su Gmail y encontré los siguientes {len(mensajes)} correos relacionados:
{correos_texto}

Tu tarea:
Escribe un mensaje directo a Yerko por Telegram.
1. Responde su pregunta, resumiendo lo que encontraste en estos correos.
2. Si le están pidiendo algo a él, destácalo.
3. Sé concisa y amigable. No inventes cosas que no están ahí.

Escribe SÓLO la respuesta final que se enviará a Telegram.
"""
    client = Groq(api_key=GROQ_API_KEY)
    
    try:
        respuesta = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        mensaje_final = respuesta.choices[0].message.content
        enviar_telegram(mensaje_final)
    except Exception as e:
        enviar_telegram("❌ Encontré los correos, pero falló mi conexión neuronal (Groq) al intentar resumirlos.")
        print(e)


if __name__ == "__main__":
    # Recibirá argumentos tipo: "from:paula newer_than:2d" "correos recientes de paula"
    if len(sys.argv) >= 3:
        query = sys.argv[1]
        desc = sys.argv[2]
        analizar_correo_dinamico(query, desc)
    else:
        print("Faltan argumentos (query_gmail, descripcion_usuario)")
