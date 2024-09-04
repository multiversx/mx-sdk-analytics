from datetime import datetime, timedelta
from functools import reduce
import json
# from pathlib import Path
from typing import Any, Dict, List
from bs4 import BeautifulSoup, Tag
import requests
from tqdm import tqdm

from utils import Language, PackagesRegistry, Reports
from constants import CRATES_SEARCH_PREFIX, DAYS_IN_MONTHLY_REPORT, NPM_SEARCH_PREFIX, PYPI_SEARCH_PREFIX, DATE_FORMAT
from fetcher import DailyDownloads, FetcherObject, PackageObject, ScoreObject


class PackageRegistryDailyDownloads(DailyDownloads):
    @staticmethod
    def from_npm_fetched_data(response: Dict[str, Any]) -> 'PackageRegistryDailyDownloads':
        result = PackageRegistryDailyDownloads()
        result.date = response.get('day', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result

    @staticmethod
    def from_pypi_fetched_data(response: Dict[str, Any]) -> 'PackageRegistryDailyDownloads':
        result = PackageRegistryDailyDownloads()
        result.date = response.get('date', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result

    @staticmethod
    def from_crates_fetched_data(response: Dict[str, Any]) -> 'PackageRegistryDailyDownloads':
        result = PackageRegistryDailyDownloads()
        result.date = response.get('date', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result


class PackageRegistryPackageObject(PackageObject):

    @staticmethod
    def from_npm_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageRegistryPackageObject':
        result = PackageRegistryPackageObject()
        raw_downloads = response.get('downloads', [])
        result.downloads = [PackageRegistryDailyDownloads.from_npm_fetched_data(
            item) for item in raw_downloads]
        result.package_name = response.get('package', package)
        result.package_language = lang
        result.package_site = PackagesRegistry.NPM.repo_name
        result.no_of_downloads = reduce(
            lambda acc, dd: acc + dd.downloads, result.downloads, 0)
        return result

    @staticmethod
    def from_crates_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageRegistryPackageObject':
        def add_or_update_downloads(my_list: List[PackageRegistryDailyDownloads], elem: PackageRegistryDailyDownloads):
            if elem.date in map(lambda x: x.date, my_list):
                existing_item = next(
                    item for item in my_list if item.date == elem.date)
                existing_item.downloads += elem.downloads
            else:
                my_list.append(elem)

        result = PackageRegistryPackageObject()
        raw_downloads = response.get('version_downloads', [])

        for elem in raw_downloads:
            new_download_data = PackageRegistryDailyDownloads.from_crates_fetched_data(elem)
            add_or_update_downloads(result.downloads, new_download_data)
        raw_downloads = response.get("meta", {}).get("extra_downloads", [])

        for elem in raw_downloads:
            new_download_data = PackageRegistryDailyDownloads.from_crates_fetched_data(elem)
            add_or_update_downloads(result.downloads, new_download_data)

        result.package_language = lang
        result.package_name = package
        result.package_site = PackagesRegistry.CARGO.repo_name
        result.no_of_downloads = reduce(
            lambda acc, dd: acc + dd.downloads, result.downloads, 0)
        return result

    @staticmethod
    def from_pypi_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageRegistryPackageObject':
        result = PackageRegistryPackageObject()
        raw_downloads = response.get('data', [])
        result.downloads = [PackageRegistryDailyDownloads.from_pypi_fetched_data(item) for item in filter(
            lambda x: x.get('category', '') == "with_mirrors", raw_downloads)]
        result.package_language = lang
        result.package_name = response.get('package', package)
        result.package_site = PackagesRegistry.PYPI.repo_name
        result.no_of_downloads = reduce(
            lambda acc, dd: acc + dd.downloads, result.downloads, 0)
        return result

    @property
    def daily_activity_type(self):
        return PackageRegistryDailyDownloads


class PackageRegistryFetcherObject(FetcherObject):
    def write_report(self):
        super().write_report("rep")

    def write_json(self):
        super().write_json(repo_type=Reports.BLUE.value)

    def create_summary_statistics_from_daily_downloads(self, end_date: str) -> Dict[str, Any]:
        return super().create_summary_statistics_from_daily_downloads(end_date, report_duration=DAYS_IN_MONTHLY_REPORT)

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

    def fetch_npm_downloads(self, package_name: str):
        url = f"https://api.npmjs.org/downloads/range/{self.start_date}:{self.end_date}/{package_name}"
        response = requests.get(url)
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
            soup = BeautifulSoup(response.text, "html.parser")
            package_info = [item for item in soup.find_all("a", class_="package-snippet")]
            new_package_names = [item.find("span", class_="package-snippet__name").text.strip() for item in package_info]
            if not new_package_names:
                break
            new_package_names = [item for item in new_package_names if pattern in item]
            package_names.extend(new_package_names)
            if not new_package_names:
                break
            page += 1
        return package_names

    def fetch_pypi_package_score(self, package_name: str) -> json:
        score_details = {}
        url = f"https://snyk.io/advisor/python/{package_name}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tags: List[Tag] = [item for item in soup.find_all('title')]
            for title_tag in title_tags:
                title_text = title_tag.text
                if "package health:" in title_text.lower():
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

    @property
    def package_class(self):
        return PackageRegistryPackageObject

    @staticmethod
    def from_package_sites(date: str) -> 'PackageRegistryFetcherObject':
        result = PackageRegistryFetcherObject()
        end_date = datetime.strptime(date, DATE_FORMAT)
        start_date = end_date - timedelta(DAYS_IN_MONTHLY_REPORT - 1)
        result.start_date = start_date.strftime(DATE_FORMAT)
        result.end_date = date

        print("fetching from npm ...")
        packages = result.get_npm_package_names(NPM_SEARCH_PREFIX)
        with tqdm(total=len(packages)) as pbar:
            for package_name in packages.keys():
                fetched_downloads = result.fetch_npm_downloads(package_name)
                package_downloads = PackageRegistryPackageObject.from_npm_fetched_data(
                    package_name, Language.JAVASCRIPT.value, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistry.NPM.name)
                package_downloads.site_score = ScoreObject.from_json(packages[package_name])
                result.downloads.append(package_downloads)
                pbar.update(1)

        print("fetching from crates ...")
        packages = result.get_crates_package_names(CRATES_SEARCH_PREFIX)
        with tqdm(total=len(packages)) as pbar:
            for package_name in packages:
                fetched_downloads = result.fetch_crates_downloads(package_name)
                package_downloads = PackageRegistryPackageObject.from_crates_fetched_data(
                    package_name, Language.RUST.value, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistry.CARGO.name)
                result.downloads.append(package_downloads)
                pbar.update(1)

        print("fetching from pypi ...")
        packages = result.get_pypi_package_names(PYPI_SEARCH_PREFIX)
        with tqdm(total=len(packages)) as pbar:
            for package_name in packages:
                fetched_downloads = result.fetch_pypi_downloads(package_name)
                package_downloads = PackageRegistryPackageObject.from_pypi_fetched_data(
                    package_name, Language.PYTHON.value, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistry.PYPI.name)
                package_downloads.site_score = ScoreObject.from_json(result.fetch_pypi_package_score(package_name))
                result.downloads.append(package_downloads)
                pbar.update(1)
        return result
