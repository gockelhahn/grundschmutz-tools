from io import StringIO
from lxml import html
from lxml.etree import ElementTree
import requests


def download_binary(url: str, dest: str) -> None:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def clean_gap(text: str) -> str:
    return text.replace(u'\xa0', ' ')


def get_html(text: str) -> ElementTree:
    # parse into xml tree
    tree = html.parse(StringIO(text))

    return tree


def get_html_from_file(path: str) -> ElementTree:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    return get_html(text)
