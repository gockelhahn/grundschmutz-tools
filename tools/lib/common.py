from io import StringIO
import json
from typing import Optional

from lxml import html
from lxml.etree import ElementTree
import pandas
import requests


def download_binary(url: str, dest: str) -> None:
    print('Downloading: {}'.format(url))
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def clean_gap(text: str) -> str:
    return text.replace(u'\xa0', ' ')


def get_from_json(filename: str, attr: str, value: str) -> [int, ValueError]:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        for elem in data:
            if attr in elem and elem[attr] == value:
                return elem['id']

    raise ValueError('No item found with "{}"@"{}" inside {}'
                     .format(value, attr, filename))


def save_json(filename: str, elements: list) -> None:
    with open(filename, 'w') as f:
        f.write('[\n  %s\n]\n' % ',\n  '.join(
            json.dumps(obj, ensure_ascii=False, separators=(', ', ': '))
                for obj in elements))


def get_html(text: str) -> ElementTree:
    # parse into xml tree
    tree = html.parse(StringIO(text))

    return tree


def get_html_from_file(path: str) -> ElementTree:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    return get_html(text)


def get_dataframe_from_csv(path: str,
                           prepend_text: Optional[str] = '',
                           skip_lines: Optional[int] = 0,
                           sep: Optional[str] = ',') -> pandas.DataFrame:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # skip lines (headers)
    text = '\n'.join(text.splitlines()[skip_lines:])
    # add some other header before the lines
    text = prepend_text + text

    # read into a pandas dataframe
    df = pandas.read_csv(StringIO(text),
                         sep=sep,
                         dtype=str,
                         # skip NaN values
                         na_values=[],
                         keep_default_na=False)

    return df
