# core/config.py
import os

ADAMSPAY_API_KEY = os.getenv("ADAMSPAY_API_KEY", "cambia_esto")
ADAMSPAY_ENV = os.getenv("ADAMSPAY_ENV", "staging").lower()  # 'staging' | 'production'

if ADAMSPAY_ENV == "production":
    ADAMSPAY_BASE = "checkout.adamspay.com"
    ADAMSPAY_API_PREFIX = "/api/v1"
else:
    ADAMSPAY_BASE = "staging.adamspay.com"
    ADAMSPAY_API_PREFIX = "/api/v1"

# Webhook (si usan firma HMAC o token propio, ajustá aquí)
WEBHOOK_SIGNATURE_HEADER = os.getenv("WEBHOOK_SIGNATURE_HEADER", "")       # ej: X-Adams-Signature (si existiera)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")                           # opcional; si no, dejar vacío

# Formato de docId: acá usamos el patrón del sistema viejo
def make_doc_id(order_id: int) -> str:
    return f"order-{order_id}"
