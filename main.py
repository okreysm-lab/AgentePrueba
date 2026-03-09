import requests
import json
import feedparser
import yt_dlp
from googletrans import Translator
from datetime import datetime


# ==============================
# TELEGRAM
# ==============================


def enviar_telegram(mensaje):

    token = "8778043651:AAHtmw2cjFyqaIf4GeG6PEK0xBOu38zPUFQ"
    chat_id = "8727442796"

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": mensaje[:4000]
    }

    requests.post(url, data=data)


# ==============================
# TRADUCTOR
# ==============================

def traducir(texto):

    translator = Translator()

    try:
        return translator.translate(texto, dest="es").text
    except:
        return texto


# ==============================
# CARGAR TAREAS
# ==============================

def load_tasks(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        return file.readlines()


# ==============================
# CLASIFICAR TAREAS
# ==============================

def classify_tasks(tasks):

    urgente = []
    pendiente = []
    seguimiento = []
    informativo = []

    for task in tasks:

        t = task.strip().lower()

        if "urgente" in t:
            urgente.append(task)

        elif "pendiente" in t:
            pendiente.append(task)

        elif "seguimiento" in t:
            seguimiento.append(task)

        elif "informativo" in t:
            informativo.append(task)

        else:
            pendiente.append(task)

    return urgente, pendiente, seguimiento, informativo


# ==============================
# GENERAR AGENDA
# ==============================

def generar_agenda(urgente, pendiente, seguimiento, informativo):

    texto = "📊 AGENDA\n\n"

    texto += "🚨 Urgente\n"
    for t in urgente:
        texto += f"• {t}"

    texto += "\n📌 Pendiente\n"
    for t in pendiente:
        texto += f"• {t}"

    texto += "\n🔎 Seguimiento\n"
    for t in seguimiento:
        texto += f"• {t}"

    texto += "\nℹ️ Informativo\n"
    for t in informativo:
        texto += f"• {t}"

    return texto


# ==============================
# NOTICIAS IA
# ==============================

def get_ai_news():

    feeds = [

        "https://openai.com/blog/rss.xml",
        "https://deepmind.google/blog/rss.xml",
        "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "https://the-decoder.com/feed/",
        "https://venturebeat.com/category/ai/feed/"

    ]

    noticias = []

    for feed in feeds:

        d = feedparser.parse(feed)

        for entry in d.entries[:2]:

            titulo = traducir(entry.title)
            link = entry.link

            noticias.append(f"{titulo}\n{link}")

    return noticias[:8]


# ==============================
# VIDEOS IA
# ==============================

def get_youtube_ai_videos():

    channels = [

        "https://www.youtube.com/@TwoMinutePapers/videos",
        "https://www.youtube.com/@AIExplained/videos",
        "https://www.youtube.com/@YannicKilcher/videos",
        "https://www.youtube.com/@Fireship/videos"

    ]

    ydl_opts = {

        "quiet": True,
        "extract_flat": True

    }

    videos = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        for channel in channels:

            info = ydl.extract_info(channel, download=False)

            for video in info["entries"][:2]:

                titulo = traducir(video["title"])
                link = f"https://youtube.com/watch?v={video['id']}"

                videos.append(f"{titulo}\n{link}")

    return videos


# ==============================
# GUARDAR RESUMEN
# ==============================

def save_summary(file_path, summary):

    with open(file_path, "w", encoding="utf-8") as file:

        file.write(summary)


# ==============================
# CONFIG
# ==============================

config = {

    "tareas_file": "tareas.md",
    "resumen_file": "resumen_diario.md"

}


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    tasks = load_tasks(config["tareas_file"])

    urgente, pendiente, seguimiento, informativo = classify_tasks(tasks)

    agenda = generar_agenda(urgente, pendiente, seguimiento, informativo)

    noticias = get_ai_news()

    videos = get_youtube_ai_videos()

    hoy = datetime.now().strftime("%d %B %Y")

    mensaje = f"""
👋 Hola amo Yerko, Trinity por acá.

📅 {hoy}

━━━━━━━━━━━━━━━━

{agenda}

━━━━━━━━━━━━━━━━

🧠 RADAR IA

"""

    for n in noticias:

        mensaje += f"\n{n}\n"

    mensaje += "\n━━━━━━━━━━━━━━━━\n\n🎥 VIDEOS IA\n"

    for v in videos:

        mensaje += f"\n{v}\n"

    save_summary(config["resumen_file"], mensaje)

    enviar_telegram(mensaje)

    print("Resumen enviado a Telegram")