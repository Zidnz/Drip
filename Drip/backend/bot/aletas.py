import requests

TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

def enviar_telegram(mensaje):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": mensaje
    })