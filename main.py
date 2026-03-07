import json
import re

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

# Guardar resumen diario en resumen_diario.md
def save_summary(file_path, summary):
    with open(file_path, 'w') as file:
        file.write(summary)

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
    save_summary(config["resumen_file"], summary)
