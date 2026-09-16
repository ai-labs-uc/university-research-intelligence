from urllib.parse import urljoin, urlsplit

import requests

from bs4 import BeautifulSoup

from app.etl.utils import clean_text


HEADERS = {
    "User-Agent":
        "Mozilla/5.0 Research Intelligence Bot"
}



IGNORE_LINK_TEXT = [

    "home",
    "news",
    "events",
    "calls and events",
    "announcement",
    "memorandum",
    "issuance",
    "contact",
    "about",
    "archive"

]


def is_valid_link(text):

    text = text.lower()


    for word in IGNORE_LINK_TEXT:

        if word in text:

            return False


    return True




def discover_links(source):


    response = requests.get(
        source["listing_url"],
        headers=HEADERS,
        timeout=30,
        verify=False
    )


    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "lxml"
    )


    host = urlsplit(
        source["listing_url"]
    ).netloc


    links = set()


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
        )



        if not is_valid_link(text):

            continue



        links.add(url)



    return list(links)




def fetch_page(url):


    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        verify=False
    )


    response.raise_for_status()



    soup = BeautifulSoup(
        response.text,
        "lxml"
    )



    title_node = (
        soup.find("h1")
        or soup.find("title")
    )


    title = clean_text(

        title_node.get_text(
            " ",
            strip=True
        )
        if title_node
        else url

    )


    content = clean_text(

        soup.get_text(
            "\n",
            strip=True
        )

    )


    return title, content