import os
from datetime import timedelta

from minio import Minio

from src.core.config import settings


BUCKETS = {
    "reports": "Сгенерированные отчеты",
    "exports": "Экспортированные данные",
    "imports": "Загруженные файлы для импорта",
}


class MinIOService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def upload_file(
        self,
        bucket: str,
        file_path: str,
        object_name: str | None = None,
        expires_days: int = 7,
    ) -> str:
        """
        Загрузить файл в MinIO.

        Returns:
            Pre-signed URL для скачивания
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        self.client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
            content_type=self._get_content_type(file_path),
        )

        return self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(days=expires_days),
        )

    def download_file(self, bucket: str, object_name: str, file_path: str) -> None:
        """Скачать файл из MinIO."""
        self.client.fget_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
        )

    def delete_file(self, bucket: str, object_name: str) -> None:
        """Удалить файл."""
        self.client.remove_object(bucket, object_name)

    def list_files(self, bucket: str, prefix: str | None = None):
        """Список файлов."""
        return self.client.list_objects(
            bucket_name=bucket,
            prefix=prefix,
            recursive=True,
        )

    def _get_content_type(self, file_path: str) -> str:
        """Определить Content-Type по расширению файла."""
        ext = os.path.splitext(file_path)[1].lower()

        content_types = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".csv": "text/csv",
            ".pdf": "application/pdf",
            ".json": "application/json",
        }

        return content_types.get(ext, "application/octet-stream")
