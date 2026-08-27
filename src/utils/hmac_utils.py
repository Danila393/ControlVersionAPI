import hashlib
import hmac
import json


def sign_payload(payload: dict, secret_key: str) -> str:
    """
    Подписывает payload по HMAC-SHA256 — тот же механизм, что используют
    GitHub/Stripe для своих вебхуков. Получатель на своей стороне пересчитывает
    подпись тем же secret_key и сверяет с тем, что пришло в заголовке —
    так он убеждается, что запрос реально от нас, а не подделан кем-то, кто
    просто знает наш URL.

    sort_keys=True важен: без него порядок ключей в JSON не гарантирован,
    и одна и та же логическая структура данных могла бы дать разную подпись.
    """
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_signature(payload: dict, secret_key: str, signature: str) -> bool:
    """
    hmac.compare_digest, а не обычное `==` — специально устойчиво к timing-атакам
    (обычное сравнение строк прерывается на первом несовпадающем символе, и по
    времени ответа теоретически можно подобрать подпись побайтово).
    """
    expected = sign_payload(payload, secret_key)
    return hmac.compare_digest(expected, signature)
