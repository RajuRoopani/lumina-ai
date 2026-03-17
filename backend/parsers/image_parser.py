import base64
from typing import Optional
import anthropic
from config import ANTHROPIC_API_KEY

_client: Optional[anthropic.Anthropic] = None

def _get_client() -> "anthropic.Anthropic":
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client

MEDIA_MAP = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png", "gif": "image/gif", "webp": "image/webp",
}

def parse_image(file_path: str) -> str:
    """Use Claude vision to extract text and describe visual content from an image."""
    try:
        with open(file_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    except OSError as e:
        raise ValueError(f"Cannot read image file '{file_path}': {e}") from e

    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    media_type = MEDIA_MAP.get(ext, "image/png")

    try:
        message = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": "Extract all text and describe all diagrams, tables, and visual content from this image. Be thorough and structured."}
                ]
            }]
        )
    except anthropic.APIError as e:
        raise ValueError(f"Claude vision API error: {e}") from e

    if not message.content:
        raise ValueError("Claude vision returned an empty response")
    return message.content[0].text
