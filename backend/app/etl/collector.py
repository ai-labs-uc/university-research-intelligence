from urllib.parse import urljoin, urlsplit

import requests

from bs4 import BeautifulSoup

from app.etl.utils import clean_text


HEADERS = {

    "User-Agent":
    (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    ),

    "Accept":
    "text/html,application/xhtml+xml"

}



def get_page(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        verify=False
    )

    response.raise_for_status()

    return response.text



def discover_links(source: dict):

    html = get_page(
        source["listing_url"]
    )


    soup = BeautifulSoup(
        html,
        "lxml"
    )


    host = urlsplit(
        source["listing_url"]
    ).netloc


    keywords = source.get(
        "keywords",
        []
    )


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

    html = get_page(url)


    soup = BeautifulSoup(
        html,
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


    text = soup.get_text(
        "\n",
        strip=True
    )


    return title, text