from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import subprocess
import json

app = FastAPI()

# Allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"

SYSTEM_PROMPT = """
You are TARS — a local AI system controller.

If the user wants to perform a system action,
respond ONLY in pure JSON format like this:

{
  "action": "open_explorer"
}

Available actions:
- open_explorer
- open_chrome
- open_vscode

If no system action is requested,
respond normally in plain text.

IMPORTANT:
Do NOT wrap JSON in markdown.
Do NOT use ```json formatting.
Return only raw JSON when triggering an action.
"""

@app.post("/chat")
async def chat(data: dict):

    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": "google/gemma-3n-e4b",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                *data["messages"]
            ],
            "temperature": 0.3
        }
    )

    result = response.json()
    reply = result["choices"][0]["message"]["content"]

    # Clean formatting if model still adds markdown
    clean_reply = reply.strip()

    if clean_reply.startswith("```"):
        clean_reply = clean_reply.replace("```json", "").replace("```", "").strip()

    # Try parsing JSON action
    try:
        parsed = json.loads(clean_reply)

        if "action" in parsed:

            if parsed["action"] == "open_explorer":
                subprocess.Popen("explorer")
                return {"choices":[{"message":{"content":"Opening File Explorer."}}]}

            elif parsed["action"] == "open_chrome":
                subprocess.Popen("start chrome", shell=True)
                return {"choices":[{"message":{"content":"Opening Chrome."}}]}

            elif parsed["action"] == "open_vscode":
                subprocess.Popen("code", shell=True)
                return {"choices":[{"message":{"content":"Opening VS Code."}}]}

    except:
        pass

    # If no action, return normal model reply
    return result
