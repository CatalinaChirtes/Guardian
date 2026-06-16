import os

from supabase import create_client, Client

from app.config import settings

BUCKET_NAME = "curriculum-files"
INDEX_BUCKET = "faiss-index"

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


def _ensure_bucket(client: Client, bucket: str) -> None:
    try:
        client.storage.get_bucket(bucket)
    except Exception:
        client.storage.create_bucket(bucket, options={"public": False})


def upload_file(file_path: str, storage_path: str) -> str:
    client = _get_client()
    _ensure_bucket(client, BUCKET_NAME)
    with open(file_path, "rb") as f:
        client.storage.from_(BUCKET_NAME).upload(
            storage_path, f.read(), {"content-type": "application/octet-stream", "upsert": "true"}
        )
    return storage_path


def download_file(storage_path: str, local_path: str) -> str:
    client = _get_client()
    data = client.storage.from_(BUCKET_NAME).download(storage_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(data)
    return local_path


def delete_file(storage_path: str) -> None:
    client = _get_client()
    try:
        client.storage.from_(BUCKET_NAME).remove([storage_path])
    except Exception:
        pass


def upload_index(local_index_dir: str) -> None:
    client = _get_client()
    _ensure_bucket(client, INDEX_BUCKET)
    for filename in os.listdir(local_index_dir):
        filepath = os.path.join(local_index_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, "rb") as f:
                client.storage.from_(INDEX_BUCKET).upload(
                    filename, f.read(),
                    {"content-type": "application/octet-stream", "upsert": "true"},
                )


def download_index(local_index_dir: str) -> bool:
    client = _get_client()
    try:
        files = client.storage.from_(INDEX_BUCKET).list()
    except Exception:
        return False

    if not files:
        return False

    os.makedirs(local_index_dir, exist_ok=True)
    for file_info in files:
        name = file_info["name"]
        data = client.storage.from_(INDEX_BUCKET).download(name)
        with open(os.path.join(local_index_dir, name), "wb") as f:
            f.write(data)
    return True


def clear_index() -> None:
    client = _get_client()
    try:
        files = client.storage.from_(INDEX_BUCKET).list()
        if files:
            names = [f["name"] for f in files]
            client.storage.from_(INDEX_BUCKET).remove(names)
    except Exception:
        pass
