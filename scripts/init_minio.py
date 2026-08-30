"""
Разовый скрипт: создаёт в MinIO бакеты, нужные проекту (reports/exports/imports),
если их ещё нет. Запускать вручную после того, как контейнер minio поднят:

    python -m scripts.init_minio
"""

from src.storage.minio_service import BUCKETS, MinIOService


def initialize_minio_buckets() -> None:
    service = MinIOService()

    for bucket_name in BUCKETS:
        if not service.client.bucket_exists(bucket_name):
            service.client.make_bucket(bucket_name)
            print(f"created bucket: {bucket_name}")
        else:
            print(f"bucket already exists: {bucket_name}")


if __name__ == "__main__":
    initialize_minio_buckets()
