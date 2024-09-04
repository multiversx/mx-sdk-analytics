import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

from constants import (CRATES_SEARCH_PREFIX, DATE_FORMAT,
                       DAYS_IN_MONTHLY_REPORT, DAYS_IN_WEEK, NPM_SEARCH_PREFIX,
                       PYPI_SEARCH_PREFIX)
from utils import Language, PackagesRegistry

# in order to allow calculations of scores in future implementations, the score must be a dictionary of individual composite scores
# the general score is calculated as a weighted means of composite scores, which in turn will be weighted means of individual scores.
#
# NPM: final_score = weightedMean([[quality, 6],[popularity, 7],[maintenance, 7]]);
# NPM: quality = weightedMean([[carefulness, 7],[tests, 7],[health, 4],[branding, 2]]);
# NPM: maintanance = weightedMean([[releasesFrequency, 2],[commitsFrequency, 1],[openIssues, 1],[issuesDistribution, 2]]);
# NPM: popularity = weightedMean([[communityInterest, 2],[downloadsCount, 2],[downloadsAcceleration, 1],// [scores.dependentsCount, 2]]);
# PYPI: health_score = weightedMean([[security, 6],[popularity, 6],[maintanance, 4],[community, 4]]);


class Score:
    def __init__(self) -> None:
        self.final: float = 0
        self.detail: Dict[str, Any] = {}

    def __repr__(self) -> str:
        return ', '.join(f"{key} = {float(value):.2f}" if isinstance(value, (float, int)) else f"{key} = {value}" for key, value in self.detail.items())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'final': self.final,
            'detail': self.detail
        }

    @staticmethod
    def from_json(info: Dict[str, Any]) -> 'Score':
        response = Score()
        response.final = info.get('final', 0)
        response.detail = info.get('detail', {})
        return response


class DailyDownloads:
    def __init__(self) -> None:
        self.date = '1980-01-01'
        self.downloads = 0

    def __str__(self) -> str:
        return f"{self.date} - {self.downloads} downloads"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date,
            'downloads': self.downloads
        }

    @staticmethod
    def from_npm_fetched_data(response: Dict[str, Any]) -> 'DailyDownloads':
        result = DailyDownloads()
        result.date = response.get('day', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result

    @staticmethod
    def from_pypi_fetched_data(response: Dict[str, Any]) -> 'DailyDownloads':
        result = DailyDownloads()
        result.date = response.get('date', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result

    @staticmethod
    def from_crates_fetched_data(response: Dict[str, Any]) -> 'DailyDownloads':
        result = DailyDownloads()
        result.date = response.get('date', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result

    @staticmethod
    def from_json_file(response: Dict[str, Any]):
        result = DailyDownloads()
        result.date = response.get('date', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result


class PackageDownloads:
    def __init__(self) -> None:
        self.package_name = ''
        self.package_language = ''
        self.package_site = ''
        self.downloads: List[DailyDownloads] = []
        self.no_of_downloads = 0
        self.libraries_io_score: json = {}
        self.site_score = Score()

    def __str__(self):
        print_str = f"PACKAGE = {self.package_name} - language = {self.package_language} - site = {self.package_site} - downloads = {self.no_of_downloads}\n"
        print_str += "\n".join(str(item) for item in self.downloads)
        print_str += "\n"
        return print_str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metadata': {
                'section_name': self.package_site,
                'package_name': self.package_name,
                'language': self.package_language,
                'no_of_downloads': self.no_of_downloads,
                'libraries_io_score': self.libraries_io_score,
                'site_score': self.site_score.to_dict()
            },
            'downloads': [item.to_dict() for item in self.downloads]
        }

    def create_summary_of_monthly_statistics_from_daily_downloads(self, end_date: str) -> Dict[str, Any]:
        last_month_downloads = sum(dd.downloads for dd in self.downloads)
        avg_daily_downloads = last_month_downloads / DAYS_IN_MONTHLY_REPORT
        seven_days_before = (datetime.strptime(end_date, DATE_FORMAT).date() - timedelta(DAYS_IN_WEEK - 1)).strftime(DATE_FORMAT)
        last_week_downloads = sum(dd.downloads for dd in [item for item in self.downloads if item.date >= seven_days_before])
        return {
            'last_month_downloads': last_month_downloads,
            'last_week_downloads': last_week_downloads,
            'avg_daily_downloads': avg_daily_downloads,
            'libraries_io_score': sum(value for value in self.libraries_io_score.values()),
            'libraries_io_negatives': self.analyse_libraries_io_score(),
            'site_score': f"{self.site_score.final:.2f}",
            'site_score_details': repr(self.site_score)
        }

    def analyse_libraries_io_score(self):
        negatives = ', '.join(f"{key} = {value}" for key, value in self.libraries_io_score.items()
                              if value < 0 or value == 0 and "present" in key)
        return negatives

    @staticmethod
    def from_npm_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageDownloads':
        result = PackageDownloads()
        raw_downloads = response.get('downloads', [])
        result.downloads = [DailyDownloads.from_npm_fetched_data(
            item) for item in raw_downloads]
        result.package_name = response.get('package', package)
        result.package_language = lang
        result.package_site = PackagesRegistry.NPM.repo_name
        result.no_of_downloads = sum(dd.downloads for dd in result.downloads)
        return result

    @staticmethod
    def from_crates_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageDownloads':
        def add_or_update_downloads(my_list: List[DailyDownloads], elem: DailyDownloads):
            if elem.date in [item.date for item in my_list]:
                existing_item = next(
                    item for item in my_list if item.date == elem.date)
                existing_item.downloads += elem.downloads
            else:
                my_list.append(elem)

        result = PackageDownloads()
        raw_downloads = response.get('version_downloads', [])

        for elem in raw_downloads:
            new_download_data = DailyDownloads.from_crates_fetched_data(elem)
            add_or_update_downloads(result.downloads, new_download_data)
        raw_downloads = response.get('meta', {}).get('extra_downloads', [])

        for elem in raw_downloads:
            new_download_data = DailyDownloads.from_crates_fetched_data(elem)
            add_or_update_downloads(result.downloads, new_download_data)

        result.package_language = lang
        result.package_name = package
        result.package_site = PackagesRegistry.CARGO.repo_name
        result.no_of_downloads = sum(dd.downloads for dd in result.downloads)
        return result

    @staticmethod
    def from_pypi_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageDownloads':
        result = PackageDownloads()
        raw_downloads = response.get('data', [])
        result.downloads = [DailyDownloads.from_pypi_fetched_data(item) for item in filter(
            lambda x: x.get('category', '') == 'with_mirrors', raw_downloads)]
        result.package_language = lang
        result.package_name = response.get('package', package)
        result.package_site = PackagesRegistry.PYPI.repo_name
        result.no_of_downloads = sum(dd.downloads for dd in result.downloads)
        return result

    @staticmethod
    def from_json_file(response: Dict[str, Any]) -> 'PackageDownloads':
        result = PackageDownloads()
        raw_downloads = response.get('downloads', [])
        result.downloads = [DailyDownloads.from_json_file(
            item) for item in raw_downloads]
        meta: Dict[str, Any] = response.get('metadata', '')
        result.package_name = meta.get('package_name', '')
        result.package_site = meta.get('section_name', '')
        result.package_language = meta.get('language', '')
        result.no_of_downloads = meta.get('no_of_downloads', '')
        result.libraries_io_score = meta.get('libraries_io_score', {})
        result.site_score = Score.from_json(meta.get('site_score', {}))
        return result


class DownloadsFetcher:
    def __init__(self) -> None:
        self.start_date = ''
        self.end_date = ''
        self.downloads: List[PackageDownloads] = []
        self.rep_folder = os.environ.get('JSON_FOLDER')

    def __str__(self):
        print_str = f"DOWNLOADS REPORT ({self.start_date} - {self.end_date})\n\n"
        print_str += "\n".join(str(item) for item in self.downloads)
        print_str += "\n"
        return print_str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metadata': {
                'report_type': 'blue',
                'start_date': self.start_date,
                'end_date': self.end_date,
            },
            'records': [item.to_dict() for item in self.downloads]
        }

    def write_report(self):
        print("writting report ...")
        report_name = Path(self.rep_folder) / f"log{self.end_date}.txt"
        report_name.write_text(str(self))

    def write_json(self):
        print("writting json ...")
        report_name = Path(self.rep_folder) / f"blue{self.end_date}.json"
        report_name.write_text(json.dumps(self.to_dict(), indent=4))

    def get_npm_package_names(self, pattern: str) -> Dict[str, Any]:        # npm api (registry.npmjs.org) - query search result
        size = 20
        page = 0
        scores_dict = {}
        while True:
            url = f"https://registry.npmjs.org/-/v1/search?text={pattern}&size={size}&from={page * size}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            package_info = data.get('objects', [])
            # also gets npmjs scores in the form "{package_name}": {package_score}
            scores_dict.update({item.get('package', {}).get('name'): item.get('score', {}) for item in package_info
                                if pattern in item.get('package', {}).get('name')})
            if len(data['objects']) < size:
                break
            page += 1
        return scores_dict

    def fetch_npm_downloads(self, package_name: str) -> Dict[str, Any]:
        url = f"https://api.npmjs.org/downloads/range/{self.start_date}:{self.end_date}/{package_name}"
        response = requests.get(url)
        if 'not found' in response.text:
            return {}
        response.raise_for_status()
        return response.json()

    def get_crates_package_names(self, pattern: str) -> List[str]:      # crates api (crates/api) - query search result
        size = 20
        page = 0
        package_names = []

        while True:
            url = f"https://crates.io/api/v1/crates?q={pattern}&size={size}&from={page * size}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            package_info = data.get('crates', [])
            new_package_names = [item.get('name') for item in package_info if pattern in item.get('name')]
            package_names.extend(new_package_names)
            if len(data['crates']) < size:
                break
            page += 1
        return package_names

    def fetch_crates_downloads(self, package_name: str):
        url = f"https://crates.io/api/v1/crates/{package_name}/downloads"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # filtered_data = data.copy()
        data['version_downloads'] = [entry for entry in data['version_downloads'] if self.start_date <= entry['date'] <= self.end_date]
        data['meta']['extra_downloads'] = [entry for entry in data['meta']['extra_downloads'] if self.start_date <= entry['date'] <= self.end_date]
        return data

    def get_pypi_package_names(self, pattern: str) -> List[str]:        # pypi http search result scrapping
        page = 1
        package_names: List[str] = []

        while True:
            url = f"https://pypi.org/search/?q={pattern}&page={page}"
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            package_info = [item for item in soup.find_all('a', class_='package-snippet')]
            new_package_names = [item.find('span', class_='package-snippet__name').text.strip() for item in package_info]
            if not new_package_names:
                break
            new_package_names = [item for item in new_package_names if pattern in item]
            package_names.extend(new_package_names)
            if not new_package_names:
                break
            page += 1
        return package_names

    def fetch_pypi_package_score(self, package_name: str) -> Dict[str, Any]:
        score_details = {}
        url = f"https://snyk.io/advisor/python/{package_name}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tags: List[Tag] = [item for item in soup.find_all('title')]
            for title_tag in title_tags:
                title_text = title_tag.text
                if 'package health:' in title_text.lower():
                    health_score: int = title_text.split(':')[-1].split('/')[0].strip()
                    score_details['final'] = int(health_score) / 100
            score_details['detail'] = {}
            scores_list = soup.find('ul', class_='scores')
            for li in scores_list.find_all('li'):
                category = li.find('span').text.strip()
                status = li.find('span', class_='vue--pill__body').text.strip()
                score_details['detail'][category] = status
        else:
            print(f"Failed to retrieve the details webpage for package {package_name}.")
        return score_details

    def fetch_pypi_downloads(self, package_name: str):
        url = f"https://pypistats.org/api/packages/{package_name}/overall"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        data['data'] = [entry for entry in data['data']
                        if self.start_date <= entry['date'] <= self.end_date]
        return data

    def fetch_libraries_io_score(self, package_name: str, site: str) -> Dict[str, Any]:
        libraries_io_api_key = os.environ.get('LIBRARIES_IO_API_KEY')
        package = package_name.replace('/', '%2F')
        url = f"https://libraries.io/api/{site}/{package}/sourcerank?api_key={libraries_io_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def from_package_sites(date: str) -> 'DownloadsFetcher':
        result = DownloadsFetcher()
        end_date = datetime.strptime(date, DATE_FORMAT)
        start_date = end_date - timedelta(DAYS_IN_MONTHLY_REPORT - 1)
        result.start_date = start_date.strftime(DATE_FORMAT)
        result.end_date = date

        print("fetching from npm ...")
        packages = result.get_npm_package_names(NPM_SEARCH_PREFIX)
        with tqdm(total=len(packages)) as pbar:
            for package_name in packages.keys():
                fetched_downloads = result.fetch_npm_downloads(package_name)
                package_downloads = PackageDownloads.from_npm_fetched_data(
                    package_name, Language.JAVASCRIPT.value, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistry.NPM.name)
                package_downloads.site_score = Score.from_json(packages[package_name])
                result.downloads.append(package_downloads)
                pbar.update(1)

        print("fetching from crates ...")
        packages = result.get_crates_package_names(CRATES_SEARCH_PREFIX)
        with tqdm(total=len(packages)) as pbar:
            for package_name in packages:
                fetched_downloads = result.fetch_crates_downloads(package_name)
                package_downloads = PackageDownloads.from_crates_fetched_data(
                    package_name, Language.RUST.value, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistry.CARGO.name)
                result.downloads.append(package_downloads)
                pbar.update(1)

        print("fetching from pypi ...")
        packages = result.get_pypi_package_names(PYPI_SEARCH_PREFIX)
        with tqdm(total=len(packages)) as pbar:
            for package_name in packages:
                fetched_downloads = result.fetch_pypi_downloads(package_name)
                package_downloads = PackageDownloads.from_pypi_fetched_data(
                    package_name, Language.PYTHON.value, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistry.PYPI.name)
                package_downloads.site_score = Score.from_json(result.fetch_pypi_package_score(package_name))
                result.downloads.append(package_downloads)
                pbar.update(1)
        return result

    @staticmethod
    def from_json_file(file_name: str) -> 'DownloadsFetcher':
        with open(file_name, 'r') as file:
            json_data: Dict[str, Any] = json.load(file)
        result = DownloadsFetcher()
        meta: Dict[str, Any] = json_data.get('metadata')
        result.start_date = meta.get('start_date', '')
        result.end_date = meta.get('end_date', '')
        result.downloads = [PackageDownloads.from_json_file(
            item) for item in json_data.get('records', [])]
        return result
