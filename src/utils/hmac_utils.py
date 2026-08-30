import hashlib
import hmac
import json


def sign_payload(payload: dict, secret_key: str) -> str:
    """HMAC-SHA256 подпись payload'а (как у GitHub/Stripe webhooks) — получатель
    пересчитывает её тем же secret_key и сверяет с заголовком запроса."""
    # sort_keys=True — иначе непостоянный порядок ключей в JSON давал бы разную подпись
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_signature(payload: dict, secret_key: str, signature: str) -> bool:
    # hmac.compare_digest вместо == — устойчиво к timing-атакам
    expected = sign_payload(payload, secret_key)
    return hmac.compare_digest(expected, signature)
