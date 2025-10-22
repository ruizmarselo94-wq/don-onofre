# C:\Proyectos\don-onofre\backend\app\adamspay.py

import http.client
import json
import datetime
import logging

# --- Configuración ---
API_KEY = "ap-861a6fcd86bb47a04e4c709"
HOST = "staging.adamspay.com"  # cambiar a producción si corresponde
DEBTS_PATH = "/api/v1/debts"

logger = logging.getLogger("adamspay")
logging.basicConfig(level=logging.INFO)

# --- Funciones ---

def init_payment(order_id: int, total: float, label: str = None, days_valid: int = 2) -> str:
    """
    Crea una deuda en AdamsPay y devuelve la URL de pago.
    """
    doc_id = f"order-{order_id}"
    if label is None:
        label = f"Pedido #{order_id}"

    now_utc = datetime.datetime.utcnow()
    end_utc = now_utc + datetime.timedelta(days=days_valid)

    deuda = {
        "docId": doc_id,
        "label": label,
        "amount": {"currency": "PYG", "value": str(int(total))},
        "validPeriod": {
            "start": now_utc.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": end_utc.strftime("%Y-%m-%dT%H:%M:%S")
        }
    }

    payload = json.dumps({"debt": deuda}).encode("utf-8")
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json",
        "x-if-exists": "update"
    }

    conn = http.client.HTTPSConnection(HOST)
    conn.request("POST", DEBTS_PATH, payload, headers)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8")
    conn.close()

    response = json.loads(data)
    if "debt" in response:
        pay_url = response["debt"].get("payUrl")
        logger.info("Deuda creada, URL=%s", pay_url)
        return pay_url
    else:
        logger.error("Error creando deuda: %s", response.get("meta"))
        raise ValueError("No se pudo crear la deuda en AdamsPay")


def get_debt(doc_id: str) -> dict:
    """
    Consulta el estado de una deuda.
    """
    path = f"{DEBTS_PATH}/{doc_id}"
    headers = {"apikey": API_KEY}

    conn = http.client.HTTPSConnection(HOST)
    conn.request("GET", path, "", headers)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8")
    conn.close()

    response = json.loads(data)
    if "debt" in response:
        debt = response["debt"]
        status = debt.get("payStatus", {}).get("status")
        obj_status = debt.get("objStatus", {}).get("status")
        is_paid = status == "paid"
        is_active = obj_status in ["active", "alert", "success"]
        return {
            "payUrl": debt.get("payUrl"),
            "label": debt.get("label"),
            "isPaid": is_paid,
            "isActive": is_active,
            "paidTime": debt.get("payStatus", {}).get("time")
        }
    else:
        raise ValueError("No se pudo obtener la deuda")


def delete_debt(doc_id: str, notify_webhook: str = "true") -> dict:
    """
    Elimina una deuda.
    notify_webhook puede ser "true", "false" o "now".
    """
    path = f"{DEBTS_PATH}/{doc_id}"
    headers = {"apikey": API_KEY, "x-should-notify": notify_webhook}

    conn = http.client.HTTPSConnection(HOST)
    conn.request("DELETE", path, "", headers)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8")
    conn.close()

    response = json.loads(data)
    if "debt" in response:
        logger.info("Deuda borrada: %s", doc_id)
        return response["debt"]
    else:
        raise ValueError("No se pudo eliminar la deuda")


def handle_webhook(payload: dict) -> bool:
    """
    Valida que el webhook sea de una deuda pagada.
    Retorna True si debe marcar la orden como pagada.
    """
    doc_id = payload.get("docId")
    status = payload.get("status")
    
    if not doc_id or status != "paid":
        return False
    
    # Verificar en AdamsPay que la deuda está efectivamente pagada
    try:
        debt_info = get_debt(doc_id)
        return debt_info["isPaid"]
    except Exception:
        return False
