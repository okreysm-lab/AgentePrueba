import json
import os
import base64
import time
from datetime import datetime
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
TOKEN_FILE = "token.json" 
CONTEXT_FILE = "trinity_context.json"

TEMAS_INTERES = [
    "Innovación", "VR", "Realidad Virtual", "Level Up", 
    "Diseño", "Mejoras", "Estrategia", "Advisor", 
    "Agrosuper", "IACC", "Landes", "SAESA", "Cencosud",
    "Metaverse", "Horizon", "Polycam", "Multimedia", "E-learning"
]

# ===============================
# LEER CORREOS 2026 (OPTIMIZADO)
# ===============================

def leer_correos_2026_estratégicos():
    print("🧠 Trinity está buscando diamantes en tus correos del 2026...")
    
    if os.path.exists("token_agenda.json"):
        creds = Credentials.from_authorized_user_file("token_agenda.json")
    else:
        creds = Credentials.from_authorized_user_file("token.json")
        
    service = build("gmail", "v1", credentials=creds)

    temas_query = " OR ".join([f'"{t}"' for t in TEMAS_INTERES])
    query = f"after:2026/01/01 ({temas_query})"
    
    mensajes_ids = []
    results = service.users().messages().list(userId="me", q=query, maxResults=80).execute()
    mensajes_ids = results.get("messages", [])

    print(f"   Encontrados {len(mensajes_ids)} correos potenciales de alto valor.")
    
    archivo_memoria = []
    for i, msg in enumerate(mensajes_ids):
        if i % 10 == 0: print(f"      Descargando {i}/{len(mensajes_ids)}...")
        
        m = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
        
        cuerpo = ""
        payload = m.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        cuerpo = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        break
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                cuerpo = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        if not cuerpo: cuerpo = m.get("snippet", "")
        
        archivo_memoria.append({
            "fecha": headers.get("Date", ""),
            "de": headers.get("From", ""),
            "asunto": headers.get("Subject", ""),
            "contenido": cuerpo[:600] # Suficiente para captar la esencia
        })

    return archivo_memoria

# ===============================
# GROQ: DESTILAR POR LOTES (BATCHING)
# ===============================

def destilar_en_lotes(correos):
    if not correos: return {}

    lote_size = 15
    memoria_acumulada = {"proyectos": {}, "relaciones": []}
    
    client = Groq(api_key=GROQ_API_KEY)
    
    for i in range(0, len(correos), lote_size):
        lote = correos[i:i+lote_size]
        print(f"   --- Analizando lote {i//lote_size + 1} ({len(lote)} correos) ---")
        
        prompt = f"""
Eres Trinity, la memoria estratégica de Yerko.
Analiza estos correos y extrae hitos, decisiones y estados de proyectos de innovación.

RESPONDE SOLO CON JSON:
{{
  "proyectos": {{ "Nombre": {{ "estado": "...", "hitos": [] }} }},
  "relaciones": ["Persona - Rol"]
}}

CORREOS:
{json.dumps(lote, ensure_ascii=False)}
"""
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            
            # Combinar resultados
            for p, info in data.get("proyectos", {}).items():
                if p not in memoria_acumulada["proyectos"]:
                    memoria_acumulada["proyectos"][p] = info
                else:
                    memoria_acumulada["proyectos"][p]["hitos"].extend(info.get("hitos", []))
            
            memoria_acumulada["relaciones"].extend(data.get("relaciones", []))
            
            # Esperar un poco para no quemar el rate limit (RPM)
            time.sleep(2)
            
        except Exception as e:
            print(f"      ⚠️ Error en lote: {e}")

    return memoria_acumulada

# ===============================
# MAIN
# ===============================

def main():
    print("🧠 Trinity Deeper Memory Builder 2026 (Modular)")
    print("=" * 60)
    
    try:
        correos = leer_correos_2026_estratégicos()
        memoria_bruta = destilar_en_lotes(correos)
        
        # Una pasada final para Limpiar y Estructurar
        print("\n--- PASADA FINAL DE ESTRUCTURACIÓN ---")
        client = Groq(api_key=GROQ_API_KEY)
        prompt_final = f"""
Eres Trinity. Toma estos datos fragmentados y construye el JSON de memoria estratégica DEFINITIVO.
No pierdas detalles. Yerko es Líder de Innovación.

ESTRUCTURA:
{{
  "proyectos_innovacion": {{
     "Nombre": {{
        "estado_actual": "...",
        "linea_tiempo_2026": ["..."],
        "pendientes_estrategicos": ["..."]
     }}
  }},
  "contexto_equipo": {{ "Nombre": "Rol" }},
  "ultima_actualizacion": "{datetime.now().strftime('%Y-%m-%d')}"
}}

DATOS:
{json.dumps(memoria_bruta, ensure_ascii=False)}
"""
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_final}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        contexto_final = json.loads(completion.choices[0].message.content)
        
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            json.dump(contexto_final, f, ensure_ascii=False, indent=2)
            
        print(f"\n✅ Memoria PROFUNDA consolidada en {CONTEXT_FILE}")
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    main()
