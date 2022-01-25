import glob
import os
import pandas
import subprocess
from typing import Optional
import zipfile

from tools.common import download_binary


class BSI(object):
    DOWNLOAD_BASE = (
        'https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz')
    # ZIP file with separate PDFs (one PDF per Baustein)
    KOMPENDIUM_URL = (
        DOWNLOAD_BASE +
        '/Kompendium_Einzel_PDFs_2021/Zip_Datei_Edition_2021.zip'
        '?__blob=publicationFile&v=6')
    # URL for "Elementare Gefährdungen"
    GEFAEHRDUNGEN_URL = (
        DOWNLOAD_BASE +
        '/Kompendium/Elementare_Gefaehrdungen.pdf'
        '?__blob=publicationFile&v=4')
    # Kreuzreferenztabelle (xlsx)
    KRT_URL = (
        DOWNLOAD_BASE +
        '/Kompendium/krt2021_Excel.xlsx'
        '?__blob=publicationFile&v=3')
    # excel sheet name template
    EXCEL_SHEET_NAME = 'KRT_{}.xlsx'

    def __init__(self, tmpdir: Optional[str] = None) -> None:
        # all Gefahren
        self.gefahr = {}
        # all Bausteine including their Anforderungen
        self.baustein = {}
        # KRT (list of dataframes)
        self.krt = None

        # tmp dir for downloads and conversions
        self.tmpdir = tmpdir
        if tmpdir is None:
            self.tmpdir = os.path.realpath(
                os.path.join(os.path.dirname(__file__), '..', 'tmp'))
        os.makedirs(self.tmpdir, exist_ok=True)

        # kompendium zip
        self.kompendium_zip = os.path.join(
            self.tmpdir, 'Zip_Datei_Edition_2021.zip')
        # gefaehrdungen pdf
        self.gefaerdungen_pdf = os.path.join(
            self.tmpdir, 'Elementare_Gefaehrdungen.pdf')
        # kreuzreferenztabelle in excel format
        self.krt_xlsx = os.path.join(self.tmpdir, 'krt2021_Excel.xlsx')
        # tmp dir for baustein pdf and converted html files
        self.baustein_dir = os.path.join(self.tmpdir, 'bausteine')
        os.makedirs(self.baustein_dir, exist_ok=True)

    def _download(self) -> None:
        if not os.path.exists(self.kompendium_zip):
            download_binary(BSI.KOMPENDIUM_URL, self.kompendium_zip)
        if not os.path.exists(self.gefaerdungen_pdf):
            download_binary(BSI.GEFAEHRDUNGEN_URL, self.gefaerdungen_pdf)
        if not os.path.exists(self.krt_xlsx):
            download_binary(BSI.KRT_URL, self.krt_xlsx)

    def _prepare(self) -> None:
        # unzip
        with zipfile.ZipFile(self.kompendium_zip, 'r') as zf:
            zf.extractall(self.baustein_dir)

        # convert pdf to html with tool "pdf2html"
        pdfs = glob.glob(os.path.join(self.baustein_dir, '*.pdf'))
        pdfs.append(self.gefaerdungen_pdf)
        for pdf in pdfs:
            command = [
                '/usr/bin/pdftohtml',
                # single document
                '-s',
                # ingore images
                '-i',
                pdf
            ]
            p = subprocess.Popen(command)
            p.wait()

    def setup(self) -> None:
        self._download()
        self._prepare()

        # init KRT with pandas (via openpyxl)
        self.krt = pandas.read_excel(self.krt_xlsx,
                                     engine='openpyxl',
                                     # set to None to get all sheets as list
                                     sheet_name=None,
                                     dtype=str,
                                     # skip NaN values
                                     na_values=[],
                                     keep_default_na=False)
