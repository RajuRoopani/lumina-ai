import httpx
from bs4 import BeautifulSoup


def parse_url(url: str) -> str:
    """Fetch a URL and extract its main text content, stripping boilerplate tags."""
    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "DocViz/1.0"},
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise ValueError(f"Failed to fetch URL: {e}") from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove boilerplate tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else ""
    main = soup.find("main") or soup.find("article") or soup.find("body")
    text = (
        main.get_text(separator="\n", strip=True)
        if main
        else soup.get_text(separator="\n", strip=True)
    )

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    body = "\n".join(lines)
    return f"# {title}\n\n{body}" if title else body
