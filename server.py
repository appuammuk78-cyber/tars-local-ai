from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import subprocess
import json

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"


# ----------------------------
# SYSTEM COMMAND EXECUTION
# ----------------------------

def execute_system_action(user_text: str):

    text = user_text.lower().strip()

    # OPEN APP
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

    # CLOSE APP
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

    # LIST INSTALLED APPS
    if "list apps" in text or "installed apps" in text:
        try:
            result = subprocess.run(
                ["powershell", "Get-StartApps"],
                capture_output=True,
                text=True
            )
            # limit output so browser doesn’t freeze
            return result.stdout[:3000]
        except:
            return "Could not retrieve installed apps."

    return None


# ----------------------------
# CHAT ENDPOINT
# ----------------------------

@app.post("/chat")
async def chat(data: dict):

    user_message = data["messages"][-1]["content"]

    # First: check if it's a system command
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

    # Otherwise send to AI model
    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": "google/gemma-3n-e4b",
            "messages": data["messages"],
            "temperature": 0.6
        }
    )

    return response.json()
