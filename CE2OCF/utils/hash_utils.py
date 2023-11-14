import hashlib
import io
import json


def calculate_file_md5(filepath: str) -> str:
    md5_hash = hashlib.md5()  # noqa
    with open(filepath, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(8192), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()


def dump_ocf_json_to_bytes(ocf_json: dict) -> bytes:
    return json.dumps(ocf_json, ensure_ascii=False).encode()


def calculate_bytes_hash(file_contents_bytes: bytes) -> str:

    bytes_buffer = io.BytesIO(file_contents_bytes)
    bytes_buffer.seek(0)

    file_hash = hashlib.md5()  # noqa
    while chunk := bytes_buffer.read(8192):
        file_hash.update(chunk)

    return file_hash.hexdigest()
