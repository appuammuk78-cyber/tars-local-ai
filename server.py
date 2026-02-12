from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import subprocess
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"

# Shutdown confirmation state
shutdown_pending = False


def execute_system_action(user_text: str):
    global shutdown_pending

    text = user_text.lower().strip()

    # -----------------------
    # OPEN APP
    # -----------------------
    if text.startswith("open "):
        app_name = text.replace("open ", "").strip()

        try:
            subprocess.run(
                ["powershell", "Start-Process", app_name],
                check=True
            )
            return f"Opening {app_name}..."
        except:
            return f"Could not find or open '{app_name}'."

    # -----------------------
    # CLOSE APP
    # -----------------------
    if text.startswith("close "):
        app_name = text.replace("close ", "").strip()

        try:
            subprocess.run(
                ["powershell", "Stop-Process", "-Name", app_name, "-Force"],
                check=True
            )
            return f"Closing {app_name}..."
        except:
            return f"Could not close '{app_name}'."

    # -----------------------
    # LIST INSTALLED APPS
    # -----------------------
    if "list apps" in text or "installed apps" in text:
        try:
            result = subprocess.run(
                ["powershell", "Get-StartApps"],
                capture_output=True,
                text=True
            )
            return result.stdout[:3000]
        except:
            return "Could not retrieve installed apps."

    # -----------------------
    # SHOW RUNNING PROCESSES
    # -----------------------
    if "running processes" in text or "show processes" in text:
        try:
            result = subprocess.run(
                ["powershell", "Get-Process | Select-Object Name, Id"],
                capture_output=True,
                text=True
            )
            return result.stdout[:3000]
        except:
            return "Could not retrieve running processes."

    # -----------------------
    # SHUTDOWN SYSTEM (CONFIRMATION REQUIRED)
    # -----------------------
    if "shutdown system" in text or "shutdown pc" in text:
        shutdown_pending = True
        return "Shutdown requested. Type 'confirm shutdown' to proceed."

    if text == "confirm shutdown" and shutdown_pending:
        shutdown_pending = False
        subprocess.run(["shutdown", "/s", "/t", "5"])
        return "System will shut down in 5 seconds."

    # -----------------------
    # FILE CONTROL
    # -----------------------

    # List current directory
    if "list files" in text:
        try:
            files = os.listdir()
            return "\n".join(files)
        except:
            return "Could not list files."

    # Open specific file
    if text.startswith("open file "):
        file_name = text.replace("open file ", "").strip()

        if os.path.exists(file_name):
            subprocess.run(["powershell", "Start-Process", file_name])
            return f"Opening file '{file_name}'."
        else:
            return f"File '{file_name}' not found."

    return None


@app.post("/chat")
async def chat(data: dict):

    user_message = data["messages"][-1]["content"]

    system_result = execute_system_action(user_message)

    if system_result:
        return {
            "choices": [
                {
                    "message": {
                        "content": system_result
                    }
                }
            ]
        }

    # If not system command, use AI
    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": "google/gemma-3n-e4b",
            "messages": data["messages"],
            "temperature": 0.6
        }
    )

    return response.json()
