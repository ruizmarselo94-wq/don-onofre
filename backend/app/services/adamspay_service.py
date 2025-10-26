# services/adamspay_service.py
import http.client
import json
import datetime
from app.core.config import (
    ADAMSPAY_API_KEY,
    ADAMSPAY_BASE,
    ADAMSPAY_API_PREFIX,
    PUBLIC_BASE_URL,
)

DEBTS_PATH = f"{ADAMSPAY_API_PREFIX}/debts"

def _post(path: str, payload: dict, headers: dict) -> dict:
    conn = http.client.HTTPSConnection(ADAMSPAY_BASE)
    body = json.dumps(payload).encode("utf-8")
    conn.request("POST", path, body, headers)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8")
    conn.close()
    return json.loads(data or "{}")

def _get(path: str, headers: dict) -> dict:
    conn = http.client.HTTPSConnection(ADAMSPAY_BASE)
    conn.request("GET", path, "", headers)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8")
    conn.close()
    return json.loads(data or "{}")

def _delete(path: str, headers: dict) -> dict:
    conn = http.client.HTTPSConnection(ADAMSPAY_BASE)
    conn.request("DELETE", path, "", headers)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8")
    conn.close()
    return json.loads(data or "{}")

def create_debt(doc_id: str, total_pyg: float, label: str = None, days_valid: int = 2) -> str:
    """
    Crea la deuda y devuelve la payUrl.
    Incluye webhook y returnUrls cuando PUBLIC_BASE_URL está configurado.
    """
    if not label:
        label = f"Pedido #{doc_id}"

    now_utc = datetime.datetime.utcnow()
    end_utc = now_utc + datetime.timedelta(days=days_valid)

    debt = {
        "docId": doc_id,
        "label": label,
        "amount": {"currency": "PYG", "value": str(int(total_pyg))},
        "validPeriod": {
            "start": now_utc.strftime("%Y-%m-%dT%H:%M:%S"),
            "end":   end_utc.strftime("%Y-%m-%dT%H:%M:%S"),
        },
    }

    # Agregar webhook/returnUrls si tenemos URL pública
    if PUBLIC_BASE_URL:
        debt["webhook"] = {"url": f"{PUBLIC_BASE_URL}/webhooks/adams"}
        debt["returnUrls"] = {
            "success": f"{PUBLIC_BASE_URL}/",
            "failure": f"{PUBLIC_BASE_URL}/",
        }

    payload = {"debt": debt}

    headers = {
        "apikey": ADAMSPAY_API_KEY,
        "Content-Type": "application/json",
        "x-if-exists": "update",
    }

    resp = _post(DEBTS_PATH, payload, headers)
    debt_resp = resp.get("debt") or {}
    pay_url = debt_resp.get("payUrl")
    if not pay_url:
        raise ValueError(f"No se pudo crear deuda: {resp}")
    return pay_url

def read_debt(doc_id: str) -> dict:
    headers = {"apikey": ADAMSPAY_API_KEY}
    resp = _get(f"{DEBTS_PATH}/{doc_id}", headers)
    debt = resp.get("debt") or {}
    pay_status = (debt.get("payStatus") or {}).get("status")
    obj_status = (debt.get("objStatus") or {}).get("status")
    return {
        "docId": debt.get("docId"),
        "payUrl": debt.get("payUrl"),
        "payStatus": pay_status,
        "objStatus": obj_status,
    }

def delete_debt(doc_id: str, notify_webhook: str = "true") -> dict:
    headers = {"apikey": ADAMSPAY_API_KEY, "x-should-notify": notify_webhook}
    resp = _delete(f"{DEBTS_PATH}/{doc_id}", headers)
    if "debt" not in resp:
        raise ValueError(f"No se pudo eliminar deuda: {resp}")
    return resp["debt"]
