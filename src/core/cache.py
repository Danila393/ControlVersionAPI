import functools
import json

from redis.asyncio import Redis

from src.core.config import settings

redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


def _make_cache_key(key_prefix: str, args: tuple, kwargs: dict) -> str:
    # args[0] пропускаем — это self, не JSON-сериализуем и не влияет на кэш-ключ.
    # Значит вызывать закэшированные методы нужно именованными аргументами.
    parts = [key_prefix]
    parts += [str(a) for a in args[1:]]
    parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
    return ":".join(parts)


def cached(ttl: int, key_prefix: str):
    """Кэширует результат async-функции в Redis на ttl секунд. Функция должна
    возвращать JSON-сериализуемые данные (dict, list, str, int...)."""

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
    """Удаляет из кэша все ключи, начинающиеся с одного из переданных префиксов."""
    for prefix in key_prefixes:
        keys = [key async for key in redis_client.scan_iter(match=f"{prefix}*")]
        if keys:
            await redis_client.delete(*keys)
