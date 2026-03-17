import base64
import anthropic
from config import ANTHROPIC_API_KEY

MEDIA_MAP: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def parse_image(file_path: str) -> str:
    """Use Claude vision to extract all text and describe visual content in an image."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    with open(file_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    ext = file_path.rsplit(".", 1)[-1].lower()
    media_type = MEDIA_MAP.get(ext, "image/png")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract all text and describe all diagrams, tables, and visual content "
                            "from this image. Be thorough and structured."
                        ),
                    },
                ],
            }
        ],
    )
    return message.content[0].text
