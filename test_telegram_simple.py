import requests

TELEGRAM_TOKEN = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
CHAT_ID = "8727442796"

def test():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": "🔔 Yerko, ¿me recibes? Estoy verificando por qué no llegó el podcast."}
    r = requests.post(url, data=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")

if __name__ == "__main__":
    test()
