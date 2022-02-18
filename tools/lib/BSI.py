import glob
import os

import pandas
import subprocess
from typing import Optional
import zipfile

from .common import clean_gap, download_binary, get_html_from_file


class BSI(object):
    VERSION = '2021'
    DOWNLOAD_BASE = (
        'https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz')
    # ZIP file with separate PDFs (one PDF per Baustein)
    KOMPENDIUM_URL = (
        DOWNLOAD_BASE +
        '/Kompendium_Einzel_PDFs_2021/Zip_Datei_Edition_2021.zip'
        '?__blob=publicationFile&v=6')
    # overview URL with Bausteinkategorien
    OVERVIEW_URL = (
        'https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen'
        '/Standards-und-Zertifizierung/IT-Grundschutz'
        '/IT-Grundschutz-Kompendium/IT-Grundschutz-Bausteine'
        '/2021/Bausteine_Download_Edition_2021.html'
    )
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
        # all Bausteinkategorien
        self.bausteinkategorien = {}
        # all Gefaehrdungen
        self.gefaehrdungen = {}
        # all Bausteine including their Anforderungen
        self.baustein = {}
        # KRT (list of dataframes)
        self.krt = None

        # tmp dir for downloads and conversions
        self.tmpdir = tmpdir
        if tmpdir is None:
            self.tmpdir = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    '..', '..', 'tmp', self.VERSION))
        os.makedirs(self.tmpdir, exist_ok=True)

        # overview html
        self.overview_html = os.path.join(
            self.tmpdir, 'overview.html')
        # kompendium zip
        self.kompendium_zip = os.path.join(
            self.tmpdir, 'single_bausteine_pdf.zip')
        # gefaehrdungen pdf
        self.gefaerdungen_pdf = os.path.join(
            self.tmpdir, 'elementare_gefaehrdungen.pdf')
        # kreuzreferenztabelle in excel format
        self.krt_xlsx = os.path.join(self.tmpdir, 'kreuzreferenztabelle.xlsx')
        # tmp dir for baustein pdf and converted html files
        self.baustein_dir_extract = os.path.join(self.tmpdir, 'bausteine')
        os.makedirs(self.baustein_dir_extract, exist_ok=True)
        # folder of bausteine
        self.baustein_dir = self.baustein_dir_extract

    def _download(self) -> None:
        if not os.path.exists(self.overview_html):
            download_binary(self.OVERVIEW_URL, self.overview_html)
        if not os.path.exists(self.kompendium_zip):
            download_binary(self.KOMPENDIUM_URL, self.kompendium_zip)
        if not os.path.exists(self.gefaerdungen_pdf):
            download_binary(self.GEFAEHRDUNGEN_URL, self.gefaerdungen_pdf)
        if not os.path.exists(self.krt_xlsx):
            download_binary(self.KRT_URL, self.krt_xlsx)

    def _prepare(self) -> None:
        # unzip
        with zipfile.ZipFile(self.kompendium_zip, 'r') as zf:
            zf.extractall(self.baustein_dir_extract)

        # convert pdf to html with tool "pdf2html"
        pdfs = glob.glob(os.path.join(self.baustein_dir, '*.pdf'))
        pdfs.append(self.gefaerdungen_pdf)
        for pdf in pdfs:
            # delete old html files from earlier runs
            htmls = glob.glob(
                os.path.join(os.path.dirname(pdf),
                             '{}*.html'.format(os.path.splitext(pdf)[0])))
            for item in htmls:
                os.remove(item)

            command = [
                'pdftohtml',
                # single document
                '-s',
                # ingore images
                '-i',
                pdf
            ]

            p = subprocess.Popen(command)
            p.wait()

    def setup(self) -> None:
        # download Kompendium files
        self._download()
        # ... extract and convert to html
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

    def get_bausteinkategorien(self) -> dict:
        if len(self.bausteinkategorien) > 0:
            return self.bausteinkategorien

        # parse Bausteinkategorien
        # get html
        html = get_html_from_file(self.overview_html)

        for kat_link in html.xpath(
                '//div[contains(@class, "l-content-wrapper")]//h2'):
            # collect Bausteinkategorie attributes
            kat_title = kat_link.text_content().strip()
            # skip (needed for BSI 2022)
            if kat_title == 'Ähnliche Themen':
                continue
            kat_title_list = kat_title.split(': ')
            kat_name = kat_title_list[0]
            kat_label = kat_title_list[1]

            self.bausteinkategorien[
                clean_gap(kat_name)] = clean_gap(kat_label)

        return self.bausteinkategorien

    def get_gefaehrdungen(self) -> dict:
        if len(self.gefaehrdungen) > 0:
            return self.gefaehrdungen

        # parse Elementare_Gefaehrdungen toc
        file_prefix = self.gefaerdungen_pdf.split('.pdf')[0]
        # table of content
        toc_path = '{}s.html'.format(file_prefix)
        # get html
        toc_html = get_html_from_file(toc_path)

        for gef_link in toc_html.xpath('//a'):
            if gef_link.text_content().startswith('G 0'):
                # collect Gefaerdung attributes
                gef_title = gef_link.text_content().strip()
                gef_title_list = gef_title.split()
                gef_name = ' '.join(gef_title_list[:2])
                gef_number = gef_name.split('.')[1]
                gef_label = ' '.join(gef_title_list[2:])

                self.gefaehrdungen[gef_number] = {
                    'name': clean_gap(gef_name),
                    'label': clean_gap(gef_label)
                }

        return self.gefaehrdungen

    def get_bausteine_with_anforderungen(self) -> dict:
        if len(self.baustein) > 0:
            return self.baustein

        # loop through all Baustein PDFs
        for path in glob.glob(os.path.join(self.baustein_dir, '*.pdf')):
            file_prefix = path.split('.pdf')[0]
            # table of content
            toc_path = '{}s.html'.format(file_prefix)
            # content
            content_path = '{}-html.html'.format(file_prefix)
            # get html
            toc_html = get_html_from_file(toc_path)
            content_html = get_html_from_file(content_path)

            for bau_link in toc_html.xpath('//a'):
                if bau_link.text_content().startswith('IT-Grundschutz | '):
                    # collect Baustein attributes
                    bau_title = bau_link.text_content().split(
                        'IT-Grundschutz | ')[1]
                    bau_title_list = bau_title.split()
                    bau_name = bau_title_list[0]
                    bau_number = '.'.join(bau_name.split('.')[1:])
                    bau_label = ' '.join(bau_title_list[1:])
                    bau_cat = bau_name.split('.')[0]

                    anforderungen = {}
                    for anf_link in toc_html.xpath('//a'):
                        if anf_link.text_content().startswith(bau_name):
                            # collect Anforderung attributes
                            anf_title_split = anf_link.text_content().split()
                            anf_name = anf_title_split[0]
                            anf_number = anf_name.split(
                                '{}.A'.format(bau_name))[1]
                            anf_label = ' '.join(anf_title_split[1:])

                            anforderungen[anf_number] = {
                                'name': clean_gap(anf_name),
                                'label': clean_gap(anf_label)}

                    # get responsible person
                    # yes we need the NBSP character here
                    rolle = content_html.xpath(
                        '//p[starts-with(text(), '
                        '"Grundsätzlich zuständig")]/text()')
                    # if found
                    if len(rolle) > 0:
                        # sometimes the value for that key is in the same <p>
                        # split key and value
                        rolle = ' '.join(rolle[0].split(
                            'Grundsätzlich zuständig')[1:]).strip()
                        # if value not found, we need to get the next <p>
                        if len(rolle) == 0:
                            rolle = content_html.xpath(
                                '//p[starts-with(text(), '
                                '"Grundsätzlich zuständig")]'
                                '/following::p/text()')[0].strip()
                    # sometimes there is a different name for responsible
                    else:
                        rolle = content_html.xpath(
                            '//p[starts-with(text(), '
                            '"Bausteinverantwortlicher")]/text()')
                        # do the same as above
                        rolle = ' '.join(rolle[0].split(
                            'Bausteinverantwortlicher')[1:]).strip()
                        if len(rolle) == 0:
                            rolle = content_html.xpath(
                                '//p[starts-with(text(), '
                                '"Bausteinverantwortlicher")]'
                                '/following::p/text()')[0].strip()

                    # fix rolle BSI2022
                    if rolle == 'OT-Betrieb':
                        rolle = 'OT-Betrieb (Operational Technology, OT)'

                    if bau_cat not in self.baustein:
                        self.baustein[bau_cat] = {}

                    self.baustein[bau_cat][bau_number] = {
                        'name': clean_gap(bau_name),
                        'label': clean_gap(bau_label),
                        'rolle': clean_gap(rolle),
                        'anforderungen': anforderungen}

        return self.baustein

    def get_gefaehrdungen_by_anforderung(self, anf_name: str) -> dict:
        bau_name = anf_name.split('.A')[0]
        sheet_name = bau_name
        # fix errors within KRT, overseen by BSI
        if bau_name == 'INF.2':
            sheet_name = 'INF.2_'
        if anf_name == 'ORP.1.A9':
            anf_name = 'ORP.1.A09'
        # in BSI 2022, the Anforderung "APP.4.3.A24" is missing in KRT
        if self.VERSION == '2022' and anf_name == 'APP.4.3.A24':
            return {'G 0.14': 'CIA',
                    'G 0.15': 'CIA',
                    'G 0.22': 'CIA',
                    'G 0.19': 'CIA',
                    'G 0.23': 'CIA',
                    'G 0.39': 'CIA',
                    'G 0.46': 'CIA'}
        if anf_name == 'APP.4.4.A9':
            anf_name = 'APP.4.4.A09'

        sheet = self.krt[self.EXCEL_SHEET_NAME.format(sheet_name)]
        all_gefaehrdungen = [x for x in sheet.columns[3:].values.tolist()
                             if x.startswith('G')]
        values = sheet[sheet[bau_name].apply(
            lambda x: x.strip() == anf_name)].values.tolist()[0]
        checked = values[3:]

        gefaehrdungen_anf = {}
        # fix errors within KRT, overseen by BSI
        for i, value in enumerate(all_gefaehrdungen):
            newvalue = value
            newvalue = newvalue.replace('G0', 'G 0')
            newvalue = newvalue.replace('G.0', 'G 0.')
            newvalue = newvalue.replace('G 0.0', 'G 0.')
            if checked[i].lower().strip() == 'x':
                gefaehrdungen_anf[newvalue] = values[2].upper().strip()

        return gefaehrdungen_anf


class BSI2022(BSI):
    VERSION = '2022'
    DOWNLOAD_BASE = (
        'https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz')
    # ZIP file with separate PDFs (one PDF per Baustein)
    KOMPENDIUM_URL = (
        DOWNLOAD_BASE +
        '/IT-GS-Kompendium_Einzel_PDFs_2022/Zip_Datei_Edition_2022.zip'
        '?__blob=publicationFile&v=3')
    # overview URL with Bausteinkategorien
    OVERVIEW_URL = (
        'https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen'
        '/Standards-und-Zertifizierung/IT-Grundschutz'
        '/IT-Grundschutz-Kompendium/IT-Grundschutz-Bausteine'
        '/Bausteine_Download_Edition_node.html'
    )
    # Kreuzreferenztabelle (xlsx)
    KRT_URL = (
        DOWNLOAD_BASE +
        '/Kompendium/krt2022_Excel.xlsx'
        '?__blob=publicationFile&v=3')

    def __init__(self, tmpdir: Optional[str] = None) -> None:
        super().__init__(tmpdir)

        # folder of bausteine
        self.baustein_dir = os.path.join(self.baustein_dir, 'Einzeln_PDF')
