from __future__ import annotations

from pathlib import Path


CANONICAL_TEXT_ARTIFACT_ENCODING = "utf-8"
LEGACY_TEXT_ARTIFACT_ENCODINGS: tuple[str, ...] = (
    CANONICAL_TEXT_ARTIFACT_ENCODING,
    "utf-8-sig",
    "cp932",
)


def read_text_artifact(
    path: Path,
    *,
    encodings: tuple[str, ...] = LEGACY_TEXT_ARTIFACT_ENCODINGS,
    errors: str = "strict",
) -> str:
    data = path.read_bytes()
    last_error: UnicodeDecodeError | None = None

    for encoding in encodings:
        try:
            return data.decode(encoding).replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError as exc:
            last_error = exc

    if errors != "strict":
        return data.decode(encodings[0], errors=errors).replace("\r\n", "\n").replace("\r", "\n")

    if last_error is not None:
        raise last_error
    return data.decode(encodings[0])


def normalize_text_artifact_to_utf8(
    path: Path,
    *,
    encodings: tuple[str, ...] = LEGACY_TEXT_ARTIFACT_ENCODINGS,
) -> bool:
    if not path.exists() or not path.is_file():
        return False

    data = path.read_bytes()
    if _is_utf8_bytes(data):
        return False

    text = read_text_artifact(path, encodings=encodings)
    path.write_text(text, encoding=CANONICAL_TEXT_ARTIFACT_ENCODING)
    return True


def _is_utf8_bytes(data: bytes) -> bool:
    try:
        data.decode(CANONICAL_TEXT_ARTIFACT_ENCODING)
        return True
    except UnicodeDecodeError:
        return False
