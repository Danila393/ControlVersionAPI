from slowapi import Limiter
from slowapi.util import get_remote_address

# Лимит "по умолчанию" применяется ко всем эндпоинтам сразу, без правки каждого
# роутера отдельно. Ключ — IP клиента (get_remote_address); при желании потом
# можно перейти на ключ по API-токену/пользователю.
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
