import json
import requests
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

PLANNER_FILE = "planner_actual.json"

# Personas clave del equipo cuyas comunicaciones importan
PERSONAS_CLAVE = [
    "paula.olave",
    "paula",
    "javier.martinez",
    "javier",
    "elisabet.cayuleo",
    "elisabet",
    "mayerlin",
    "mlabrador",
    "karen",
    "andres.navarro",
    "jorge.lopez",
]

# Palabras que ayudan a pescar correos de proyectos
KEYWORDS_PROYECTO = "OT OR módulo OR entrega OR cliente OR instruccional OR desarrollo OR validación OR proyecto OR insumos"


# ===============================
# TELEGRAM
# ===============================

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje[:4000]}
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ Enviado a Telegram")
    except:
        print("❌ No se pudo enviar a Telegram")


# ===============================
# LEER TABLA ANTERIOR
# ===============================

def cargar_planner():
    try:
        with open(PLANNER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"📋 Tabla anterior cargada ({len(data['proyectos'])} proyectos)")
        return data
    except Exception as e:
        print(f"⚠️ No se encontró planner_actual.json: {e}")
        return {"fecha_actualizacion": "", "proyectos": []}


# ===============================
# GUARDAR TABLA NUEVA
# ===============================

def guardar_planner(contenido_json_str):
    try:
        # Intentar parsear la respuesta JSON del LLM
        data = json.loads(contenido_json_str)
        data["fecha_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
        with open(PLANNER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Planner actualizado guardado en {PLANNER_FILE}")
        return data
    except Exception as e:
        print(f"⚠️ No se pudo guardar el planner actualizado: {e}")
        return None


# ===============================
# LEER CORREOS DEL EQUIPO (última semana)
# ===============================

def leer_correos_equipo():
    print("📧 Leyendo correos del equipo (última semana)...")

    creds = Credentials.from_authorized_user_file("token.json")
    service = build("gmail", "v1", credentials=creds)

    # Filtro: correos de los últimos 7 días
    desde = (datetime.now() - timedelta(days=7)).strftime("%Y/%m/%d")

    # Buscamos correos de personas clave O con keywords de proyectos
    personas_query = " OR ".join([f"from:{p}" for p in PERSONAS_CLAVE])
    query = f"({personas_query}) after:{desde}"

    results = service.users().messages().list(
        userId="me",
        maxResults=80, # Ajustado para evitar rate limit
        q=query
    ).execute()

    mensajes = results.get("messages", [])
    print(f"   Encontrados {len(mensajes)} correos del equipo")

    correos = []
    for msg in mensajes:
        # Leer el correo completo en texto plano (no solo snippet)
        m = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
        
        # Intentar extraer el cuerpo de texto del correo
        cuerpo = ""
        payload = m.get("payload", {})
        
        # El cuerpo puede estar en parts o directamente en body
        import base64
        partes = payload.get("parts", [payload])
        for parte in partes:
            mime = parte.get("mimeType", "")
            if "text/plain" in mime or "text" in mime:
                data = parte.get("body", {}).get("data", "")
                if data:
                    try:
                        cuerpo = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        cuerpo = " ".join(cuerpo.split())[:600]  # 600 chars limpios
                        break
                    except:
                        pass
        
        # Si no se pudo leer el cuerpo, usar el snippet como fallback
        if not cuerpo:
            cuerpo = m.get("snippet", "")[:300]

        correos.append(
            f"De: {headers.get('From', '')}\n"
            f"Asunto: {headers.get('Subject', '')}\n"
            f"Contenido: {cuerpo}\n"
        )

    return correos


# ===============================
# GROQ: ACTUALIZAR TABLA
# ===============================

def actualizar_planner_con_ia(planner_anterior, correos_equipo):
    tabla_json = json.dumps(planner_anterior, ensure_ascii=False, indent=2)
    correos_texto = "\n---\n".join(correos_equipo) if correos_equipo else "No se encontraron correos del equipo esta semana."

    fecha_hoy = datetime.now().strftime("%d de %B de %Y")

    prompt = f"""
Eres Trinity, la asistente ejecutiva inteligente de Yerko Verdugo de Fundación SOFOFA.
Hoy es {fecha_hoy}.

Tu tarea es analizar los correos del equipo de la última semana y actualizar la tabla de proyectos.

EQUIPO:
- Encargados de proyecto: Paula Olave, Javier Martínez, Elisabet Cayuleo
- Subgerente (jefa de Yerko): Mayerlin Labrador
- Gestores de clientes: Karen Núñez, Andrés Navarro, Jorge López

REGLAS ABSOLUTAS PARA IDENTIFICAR PROYECTOS:
⚠️ LA OT ES EL IDENTIFICADOR PRIMARIO Y ABSOLUTO. Cuando un correo mencione una OT (ej. "OT 830", "OT830"), ese número identifica el proyecto. NUNCA uses solo el nombre de cliente o proyecto como identificador.
- Si ves "OT 830" en un correo → busca OT 830 en la tabla. Si no existe, créala.
- Si no hay OT en el correo pero sí nombre de proyecto (ej. "Landes Inocuidad") → búscalo por nombre en la tabla existente.

REGLAS PARA ACTUALIZAR LA TABLA:
1. Si un correo menciona avances en un proyecto → actualiza "estado_actual" y "proximo_paso"
2. Si aparece una OT nueva que NO está en la tabla → agrégala como proyecto nuevo (semáforo 🟡 por defecto)
3. Si un correo indica cambio de encargado → actualiza "encargado"
4. Si hay alertas o bloqueos → cambia semáforo a 🔴
5. Si hay validaciones de cliente o avances sin bloqueos → mantén 🟢 o sube el semáforo
6. Si un proyecto está terminado o cerrado → elimínalo de la tabla

TABLA ACTUAL (JSON):
{tabla_json}

CORREOS DEL EQUIPO ESTA SEMANA:
{correos_texto}

MUY IMPORTANTE - BUSCA ACTIVAMENTE:
- ¿Hay correos que mencionen OT 830? Si los encuentras, agrégala a la tabla con los datos que detectes.
- ¿Hay correos que hablen de Agrosuper? ¿De algún proyecto nuevo que no esté en la tabla?
- ¿Hay correos que digan que Elisabet reemplaza a Paula en algún proyecto?

Responde en DOS partes separadas EXACTAMENTE por la línea "|||TABLA|||":

PARTE 1: El correo listo para enviar a Mayerlin. Tono informal-profesional. Empieza con "Hola Mayer:" e incluye un párrafo de panorama general y viñetas de los puntos clave, incluyendo proyectos nuevos detectados. Firma como Trinity. Yerko es el Líder de Innovación y Advisor.

|||TABLA|||

PARTE 2: La tabla actualizada en formato JSON con la misma estructura exacta. SOLO el JSON puro, sin texto, sin explicaciones, empieza con {{ y termina con }}.
"""

    client = Groq(api_key=GROQ_API_KEY)

    print("\n--- TRINITY ANALIZANDO CORREOS Y ACTUALIZANDO PLANNER...\n(Groq Llama 3.3 70B en la nube) ---\n")

    respuesta = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=3000
    )

    contenido = respuesta.choices[0].message.content
    return contenido


# ===============================
# FORMATEAR TABLA PARA TELEGRAM
# ===============================

def formatear_tabla(proyectos):
    lineas = ["📊 *TABLA DE PROYECTOS ACTUALIZADA*\n"]
    for p in proyectos:
        lineas.append(
            f"{p['semaforo']} OT {p['ot']} | {p['cliente']} - {p['proyecto']}\n"
            f"   👤 {p['encargado']}\n"
            f"   📌 {p['estado_actual']}\n"
            f"   ➡️ {p['proximo_paso']}\n"
        )
    return "\n".join(lineas)


# ===============================
# MAIN
# ===============================

def main():
    print("🤖 Trinity Planner Inteligente")
    print("=" * 50)

    # 1. Cargar tabla anterior
    planner_anterior = cargar_planner()

    # 2. Leer correos del equipo de la última semana
    correos = leer_correos_equipo()

    # 3. Pedir a Groq que actualice el planner
    respuesta_ia = actualizar_planner_con_ia(planner_anterior, correos)

    print("\n" + "=" * 50)

    # 4. Separar texto del JSON usando el delimitador claro
    separador = "|||TABLA|||"
    if separador in respuesta_ia:
        partes = respuesta_ia.split(separador)
        correo_texto = partes[0].strip()
        json_raw = partes[1].strip()
        
        # Limpiar posible markdown ```json ... ``` que el LLM puede agregar
        if json_raw.startswith("```"):
            json_raw = json_raw.split("```")[1]
            if json_raw.startswith("json"):
                json_raw = json_raw[4:]
        json_nuevo = json_raw.strip()
    else:
        correo_texto = respuesta_ia
        json_nuevo = None
        print("⚠️ El modelo no usó el separador |||TABLA|||")

    print("📧 CORREO GENERADO:")
    print(correo_texto)

    # 5. Guardar tabla nueva en JSON
    if json_nuevo:
        planner_nuevo = guardar_planner(json_nuevo)
        if planner_nuevo:
            tabla_formateada = formatear_tabla(planner_nuevo.get("proyectos", []))
        else:
            tabla_formateada = ""
    else:
        tabla_formateada = ""

    # 6. Enviar a Telegram SOLO el texto del correo + tabla bonita (SIN JSON crudo)
    mensaje_telegram = f"📋 TRINITY PLANNER SEMANAL\n\n{correo_texto}"
    if tabla_formateada:
        mensaje_telegram += f"\n\n{tabla_formateada}"
    enviar_telegram(mensaje_telegram)

    print("\n✅ Planner semanal completado")


if __name__ == "__main__":
    main()
