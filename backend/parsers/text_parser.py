import re


def parse_text(content: str) -> str:
    """Remove markdown formatting, return plain text."""
    content = re.sub(r"#{1,6}\s+", "", content)                              # headings
    content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)                       # bold
    content = re.sub(r"\*(.+?)\*", r"\1", content)                           # italic
    content = re.sub(r"`{1,3}(.+?)`{1,3}", r"\1", content, flags=re.S)      # code
    content = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", content)                    # links
    return content.strip()
