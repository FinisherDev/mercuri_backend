'''import requests
from django.conf import settings

BASE = "https://api.flutterwave.com"
HEADERS = {
    "Authorization" : f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
    "Content-Type" : "application/json"
}

def initiate_transfer(account_number, bank_code, amount, reference, narration = "Withdrawal"):
    url = f"{BASE}/v3/transfers"
    payload = {
        "account_bank": bank_code,
        "account_number": account_number,
        "amount": amount,
        "narration": narration, 
        "currency": "NGN",
        "reference": reference,
    }
    resp = requests.post(url, json = payload, headers = HEADERS, timeout = 30)
    resp.raise_for_status()
    return resp.json()'''