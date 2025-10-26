# core/config.py
import os

ADAMSPAY_API_KEY = os.getenv("ADAMSPAY_API_KEY", "ap-861a6fcd86bb47a04e4c709")
ADAMSPAY_ENV = os.getenv("ADAMSPAY_ENV", "staging").lower()  # 'staging' | 'production'

if ADAMSPAY_ENV == "production":
    ADAMSPAY_BASE = "checkout.adamspay.com"
    ADAMSPAY_API_PREFIX = "/api/v1"
else:
    ADAMSPAY_BASE = "staging.adamspay.com"
    ADAMSPAY_API_PREFIX = "/api/v1"

# URL pública para webhook/returnUrls
# En Railway, setear: PUBLIC_BASE_URL = https://<tu-servicio>.up.railway.app
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
if PUBLIC_BASE_URL and not PUBLIC_BASE_URL.startswith(("http://", "https://")):
    PUBLIC_BASE_URL = "https://" + PUBLIC_BASE_URL

# Webhook (si usás firma/token propio, ajustar aquí)
WEBHOOK_SIGNATURE_HEADER = os.getenv("WEBHOOK_SIGNATURE_HEADER", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# Compat (no se usa al crear deudas nuevas)
def make_doc_id(order_id: int) -> str:
    return f"order-{order_id}"
