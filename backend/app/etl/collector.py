from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

from app.etl.utils import clean_text

HEADERS = {
    "User-Agent":
    "University-Research-Intelligence/1.0 (+academic research office)"
}

def discover_links(source: dict) -> list[str]:
    response = requests.get(
        source["listing_url"],
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    host = urlsplit(source["listing_url"]).netloc

    # An empty keyword list means "this whole listing page is already
    # about one topic" (e.g. a CFP aggregator whose link text is just
    # conference names, never the literal phrase "call for papers") —
    # take every same-host link instead of filtering by link text.
    keywords = source.get("keywords") or []

    links = set()

    for a in soup.find_all("a", href=True):
        url = urljoin(
            source["listing_url"],
            a["href"],
        )

        if urlsplit(url).netloc != host:
            continue

        text = clean_text(
            a.get_text(" ", strip=True)
        ).lower()

        if keywords and not any(
            keyword in text
            for keyword in keywords
        ):
            continue

        links.add(url)

    return sorted(links)

def fetch_page(url: str) -> tuple[str, str]:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "lxml",
    )

    title_node = (
        soup.find("h1")
        or soup.find("title")
    )

    title = clean_text(
        title_node.get_text(" ", strip=True)
        if title_node
        else url
    )

    text = soup.get_text(
        "\n",
        strip=True,
    )

    return title, text
