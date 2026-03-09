import os
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

TOKEN_FILE = "token.json"

def leer_hitos_anuales():
    print("📜 Extrayendo hitos históricos de Gmail...")
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build("gmail", "v1", credentials=creds)

    trimestres = [
        {"nombre": "Q2 2025", "query": "after:2025/03/01 before:2025/07/01"},
        {"nombre": "Q3 2025", "query": "after:2025/07/01 before:2025/11/01"},
        {"nombre": "Q4 2025", "query": "after:2025/11/01 before:2026/01/01"},
        {"nombre": "Q1 2026", "query": "after:2026/01/01"}
    ]

    historia_raw = {}

    for tri in trimestres:
        results = service.users().messages().list(
            userId="me", 
            q=f"{tri['query']} (Innovación OR Proyecto OR OT OR Estrategia)",
            maxResults=40
        ).execute()
        
        mensajes = results.get("messages", [])
        hitos_tri = []
        for msg in mensajes:
            m = service.users().messages().get(userId="me", id=msg["id"], format="metadata", metadataHeaders=["Subject", "Date"]).execute()
            headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
            hitos_tri.append(f"{headers.get('Date')}: {headers.get('Subject')}")
        
        historia_raw[tri["nombre"]] = hitos_tri

    with open("hitos_anuales_crudos.json", "w", encoding="utf-8") as f:
        json.dump(historia_raw, f, indent=2, ensure_ascii=False)
    print("✅ Hitos guardados en hitos_anuales_crudos.json")

if __name__ == "__main__":
    leer_hitos_anuales()
