from urllib.parse import urljoin, urlsplit

import requests

from bs4 import BeautifulSoup

from app.etl.utils import clean_text


HEADERS = {
    "User-Agent":
        "Mozilla/5.0 Research-Intelligence-System/1.0"
}


BLOCKED_WORDS = [

    "news",
    "announcement",
    "announcements",
    "memorandum",
    "issuance",
    "contact",
    "about",
    "privacy",
    "terms",
    "calls and events",
    "events",

]


def fetch_html(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        verify=False
    )

    response.raise_for_status()

    return response.text



def valid_title(title):

    value = title.lower().strip()

    for word in BLOCKED_WORDS:

        if value == word:

            return False

    return True



def discover_links(source):

    html = fetch_html(
        source["listing_url"]
    )


    soup = BeautifulSoup(
        html,
        "lxml"
    )


    host = urlsplit(
        source["listing_url"]
    ).netloc


    links = set()


    keywords = source.get(
        "keywords",
        []
    )


    for a in soup.find_all(
        "a",
        href=True
    ):

        url = urljoin(
            source["listing_url"],
            a["href"]
        )


        if urlsplit(url).netloc != host:

            continue



        text = clean_text(
            a.get_text(
                " ",
                strip=True
            )
        ).lower()



        if keywords:

            if not any(
                k.lower() in text
                for k in keywords
            ):

                continue



        links.add(url)



    return list(links)





def fetch_page(url):

    html = fetch_html(url)


    soup = BeautifulSoup(
        html,
        "lxml"
    )


    title_node = (
        soup.find("h1")
        or
        soup.find("title")
    )


    title = clean_text(

        title_node.get_text(
            " ",
            strip=True
        )
        if title_node
        else ""

    )


    if not valid_title(title):

        return "", ""



    content = clean_text(

        soup.get_text(
            "\n",
            strip=True
        )

    )


    return title, content