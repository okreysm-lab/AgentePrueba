import time
from importlib.util import find_spec
# Removed invalid import
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def test_gmail():
    print("Conectando a Gmail...")
    t0 = time.time()
    
    try:
        creds = Credentials.from_authorized_user_file("token.json")
        service = build("gmail", "v1", credentials=creds)
        
        results = service.users().messages().list(userId="me", maxResults=5, q="newer_than:4d").execute()
        mensajes = results.get("messages", [])
        
        print(f"Encontrados {len(mensajes)} mensajes.")
        
        for msg in mensajes:
            service.users().messages().get(userId="me", id=msg["id"], format="metadata", metadataHeaders=["From"]).execute()
            
        print(f"Lectura completa en {time.time()-t0:.2f} segundos.")
        
    except Exception as e:
        print(f"Error Gmail: {e}")

test_gmail()
