import json
import re
import feedparser
from datetime import datetime

# Cargar tareas desde tareas.md
def load_tasks(file_path):
    with open(file_path, 'r') as file:
        tasks = file.readlines()
    return tasks

# Cargar memoria desde memoria.json
def load_memory(file_path):
    with open(file_path, 'r') as file:
        memory = json.load(file)
    return memory

# Clasificar tareas
def classify_tasks(tasks):
    urgente = []
    pendiente = []
    seguimiento = []
    informativo = []

    for task in tasks:
        task = task.strip()
        if "urgente" in task.lower():
            urgente.append(task)
        elif "pendiente" in task.lower():
            pendiente.append(task)
        elif "seguimiento" in task.lower():
            seguimiento.append(task)
        elif "informativo" in task.lower():
            informativo.append(task)
        else:
            pendiente.append(task)

    return urgente, pendiente, seguimiento, informativo

# Generar resumen diario
def generate_daily_summary(urgente, pendiente, seguimiento, informativo):
    summary = "Resumen Diario:\n\n"
    summary += "Urgente:\n"
    for task in urgente:
        summary += f"- {task}\n"
    summary += "\nPendiente:\n"
    for task in pendiente:
        summary += f"- {task}\n"
    summary += "\nSeguimiento:\n"
    for task in seguimiento:
        summary += f"- {task}\n"
    summary += "\nInformativo:\n"
    for task in informativo:
        summary += f"- {task}\n"

    return summary

# Obtener noticias de IA desde RSS feeds
def get_ai_news():
    feeds = [
        "https://techcrunch.com/tag/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://rss.arxiv.org/rss/cs.AI",
        "https://news.ycombinator.com/rss",
        "https://huggingface.co/blog/feed.xml"
    ]

    news = set()
    detected_tools = set()

    for feed in feeds:
        d = feedparser.parse(feed)
        for entry in d.entries:
            news.add(entry.title)
            detected_tools.update(find_ai_tools(entry.title))

    save_detected_tools(detected_tools)

    return list(news)[:10]

# Detectar herramientas AI en un encabezado de noticia
def find_ai_tools(title):
    ai_tools = [
        "Llama", "GPT", "Claude", "HuggingFace", "Cursor", "Devin"
    ]
    detected_tools = set()
    for tool in ai_tools:
        if tool.lower() in title.lower():
            detected_tools.add(tool)
    return detected_tools

# Guardar herramientas AI detectadas en herramientas_ai.md
def save_detected_tools(detected_tools):
    with open("herramientas_ai.md", "w", encoding='utf-8') as file:
        file.write("Herramientas IA detectadas:\n")
        for tool in detected_tools:
            file.write(f"- {tool}\n")

# Configuración
config = {
    "tareas_file": "tareas.md",
    "memoria_file": "memoria.json",
    "resumen_file": "resumen_diario.md"
}

# Ejecución
if __name__ == "__main__":
    tasks = load_tasks(config["tareas_file"])
    memory = load_memory(config["memoria_file"])
    urgente, pendiente, seguimiento, informativo = classify_tasks(tasks)
    summary = generate_daily_summary(urgente, pendiente, seguimiento, informativo)
    ai_news = get_ai_news()
    summary += "\n\nNoticias IA:\n"
    for news in ai_news:
        summary += f"- {news}\n"
    save_summary(config["resumen_file"], summary)
