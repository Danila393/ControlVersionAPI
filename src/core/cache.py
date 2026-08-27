import functools
import json

from redis.asyncio import Redis

from src.core.config import settings

redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


def _make_cache_key(key_prefix: str, args: tuple, kwargs: dict) -> str:
    """
    Собирает ключ кэша из имени + аргументов вызова. self (первый аргумент
    у методов класса) сознательно пропускаем — он не JSON-сериализуемый
    (это сам объект сервиса) и не влияет на то, ЧТО кэшируется.
    """
    parts = [key_prefix]
    parts += [str(a) for a in args[1:]]
    parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
    return ":".join(parts)


def cached(ttl: int, key_prefix: str):
    """
    Декоратор для async-функций/методов, возвращающих JSON-сериализуемые
    данные (dict, list, str, int...). Пример:

        @cached(ttl=60, key_prefix="batches_list")
        async def list_batches(self, ...):
            ...

    Первый вызов с определёнными аргументами реально идёт в базу и кладёт
    результат в Redis на `ttl` секунд. Повторный вызов с теми же аргументами
    в течение этого времени просто отдаёт значение из Redis, не трогая базу.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = _make_cache_key(key_prefix, args, kwargs)

            cached_value = await redis_client.get(cache_key)
            if cached_value is not None:
                return json.loads(cached_value)

            result = await func(*args, **kwargs)
            await redis_client.set(cache_key, json.dumps(result), ex=ttl)
            return result

        return wrapper

    return decorator


async def invalidate(*key_prefixes: str) -> None:
    """
    Удаляет из кэша всё, что начинается с одного из переданных префиксов
    (например, invalidate("batch_detail:5", "batches_list")).
    Для точечных ключей (без wildcard) можно просто delete, а для
    "всё, что начинается с..." — ищем по шаблону через scan_iter, потому что
    Redis не умеет удалять по префиксу одной командой.
    """
    for prefix in key_prefixes:
        keys = [key async for key in redis_client.scan_iter(match=f"{prefix}*")]
        if keys:
            await redis_client.delete(*keys)
