import os, time, requests, threading
from flask import Flask                     # health endpoint for Fly
app = Flask(__name__)

BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT = os.getenv("TG_ADMIN_CHAT")

import gpt4all
model = gpt4all.GPT4All("orca-mini-3b-gguf2-q4_0.gguf")

def reply(text):
    prompt = open("agent_prompt.txt").read() + "\n\nQ: " + text + "\nA:"
    return model.generate(prompt, max_tokens=90, temp=0.3)

def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": ADMIN_CHAT, "text": text}, timeout=10)

@app.route("/")                     # Fly health check
def health():
    return "AI agent alive", 200

if __name__ == "__main__":
    # start Flask in background so Fly sees open port
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080))),
        daemon=True
    ).start()

    # Telegram polling loop
    offset = 0
    while True:
        updates = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}").json().get("result", [])
        for u in updates:
            offset = u["update_id"] + 1
            if "message" not in u: continue
            m = u["message"]
            if str(m["chat"]["id"]) != str(ADMIN_CHAT): continue
            ans = reply(m["text"])
            send_msg(ans)
        time.sleep(2)
