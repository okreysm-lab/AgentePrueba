import time
import requests
from trinity_correo import leer_correos

def test_ollama():
    try:
        print("Leyendo correos de Gmail...")
        correos = leer_correos()
        print(f"[{len(correos)} obtenidos]")
        
        contexto = "\n".join(correos)
        prompt = f"Eres Trinity. Resume:\n{contexto}"
        
        payload = {
            "model": "llama3.2:1b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0}
        }
        
        print("Enviando a Ollama...")
        t0 = time.time()
        
        r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
        
        print(f"Ollama respondió en {time.time()-t0:.2f}s")
        print(r.json().get("response", "Sin respuesta"))
        
    except Exception as e:
        print(f"Error testeando Ollama: {e}")

if __name__ == "__main__":
    test_ollama()
