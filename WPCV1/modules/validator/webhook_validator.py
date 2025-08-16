import hmac, hashlib, json, requests
from pathlib import Path

CONFIG = json.load(open("config/webhook.json"))
LOG_PATH = Path("logs/webhook_failures.log")

def verify_signature(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

def validate_webhook():
    test_payload = {
        "event": "form_submitted",
        "timestamp": "2025-08-15T12:00:00Z",
        "data": {
            "name": "Test User",
            "email": "test@example.com",
            "message": "Validator test"
        }
    }
    raw = json.dumps(test_payload)
    signature = hmac.new(CONFIG["shared_secret"].encode(), raw.encode(), hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature
    }

    try:
        res = requests.post(CONFIG["endpoint"], headers=headers, data=raw, timeout=5)
        assert res.status_code == 200, f"Unexpected status: {res.status_code}"
        print("[✓] Webhook endpoint responded correctly.")
    except Exception as e:
        LOG_PATH.write_text(f"{test_payload['timestamp']} | ERROR: {str(e)}\n")
        print(f"[✗] Webhook validation failed: {e}")

if __name__ == "__main__":
    validate_webhook()
