import time
from http import HTTPStatus
from typing import Any, Dict, List, cast

import requests
from bs4 import BeautifulSoup, Tag
from fetcher import DailyActivity, Fetcher, Package, Score
from tqdm import tqdm

from multiversx_usage_analytics_tool.constants import (DAYS_IN_MONTHLY_REPORT,
                                                       DEFAULT_DATE,
                                                       NO_OF_RETRIES,
                                                       NPM_PAGE_SIZE,
                                                       SECONDS_BEFORE_RETRY)
from multiversx_usage_analytics_tool.ecosystem import Organization
from multiversx_usage_analytics_tool.utils import (FormattedDate, Language,
                                                   PackagesRegistries, Reports,
                                                   get_environment_var)


class PackageManagersDailyActivity(DailyActivity):
    @staticmethod
    def from_npm_fetched_data(response: Dict[str, Any]) -> 'PackageManagersDailyActivity':
        result = PackageManagersDailyActivity()
        result.date = response.get('day', DEFAULT_DATE)
        result.downloads = response.get('downloads', 0)
        return result

    @staticmethod
    def from_pypi_fetched_data(response: Dict[str, Any]) -> 'PackageManagersDailyActivity':
        result = PackageManagersDailyActivity()
        result.date = response.get('date', DEFAULT_DATE)
        result.downloads = response.get('downloads', 0)
        return result

    @staticmethod
    def from_crates_fetched_data(response: Dict[str, Any]) -> 'PackageManagersDailyActivity':
        result = PackageManagersDailyActivity()
        result.date = response.get('date', DEFAULT_DATE)
        result.downloads = response.get('downloads', 0)
        return result


class PackageManagersPackage(Package):
    def __init__(self) -> None:
        super().__init__()
        self.libraries_io_score: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        temp_dict = super().to_dict()
        temp_dict['metadata']['libraries_io_score'] = self.libraries_io_score
        return temp_dict

    def analyse_libraries_io_score(self) -> str:
        negatives = ', '.join(f"{key} = {value}" for key, value in self.libraries_io_score.items()
                              if value < 0 or value == 0 and "present" in key)
        return negatives

    def create_summary_statistics_from_daily_downloads(self, end_date: str, report_duration: int = DAYS_IN_MONTHLY_REPORT) -> Dict[str, Any]:
        summary = super().create_summary_statistics_from_daily_downloads(end_date, report_duration)
        summary['libraries_io_score'] = sum(value for value in self.libraries_io_score.values())
        summary['libraries_io_negatives'] = self.analyse_libraries_io_score(),
        return summary

    def get_daily_activity(self, item: Dict[str, Any]):
        return PackageManagersDailyActivity.from_generated_file(item)

    @staticmethod
    def from_npm_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageManagersPackage':
        result = PackageManagersPackage()
        raw_downloads = response.get('downloads', [])
        result.downloads = [PackageManagersDailyActivity.from_npm_fetched_data(item) for item in raw_downloads]
        result.package_name = response.get('package', package)
        result.package_language = lang
        result.package_site = PackagesRegistries.NPM.value.repo_name
        result.no_of_downloads = sum(dd.downloads for dd in result.downloads)
        return result

    @staticmethod
    def from_crates_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageManagersPackage':
        def add_or_update_downloads(my_list: List[PackageManagersDailyActivity], elem: PackageManagersDailyActivity):
            if elem.date in [item.date for item in my_list]:
                existing_item = next(item for item in my_list if item.date == elem.date)
                existing_item.downloads += elem.downloads
            else:
                my_list.append(elem)

        result = PackageManagersPackage()
        raw_downloads = response.get('version_downloads', [])

        for elem in raw_downloads:
            new_download_data = PackageManagersDailyActivity.from_crates_fetched_data(elem)
            add_or_update_downloads(result.downloads, new_download_data)  # type: ignore
        raw_downloads = response.get('meta', {}).get('extra_downloads', [])

        for elem in raw_downloads:
            new_download_data = PackageManagersDailyActivity.from_crates_fetched_data(elem)
            add_or_update_downloads(result.downloads, new_download_data)  # type: ignore

        result.package_language = lang
        result.package_name = package
        result.package_site = PackagesRegistries.CARGO.value.repo_name
        result.no_of_downloads = sum(dd.downloads for dd in result.downloads)
        return result

    @staticmethod
    def from_pypi_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'PackageManagersPackage':
        result = PackageManagersPackage()
        raw_downloads = response.get('data', [])
        result.downloads = [PackageManagersDailyActivity.from_pypi_fetched_data(item) for item in filter(
            lambda x: x.get('category', '') == 'with_mirrors', raw_downloads)]
        result.package_language = lang
        result.package_name = response.get('package', package)
        result.package_site = PackagesRegistries.PYPI.value.repo_name
        result.no_of_downloads = sum(dd.downloads for dd in result.downloads)
        return result

    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'PackageManagersPackage':
        result = cast(PackageManagersPackage, super().from_generated_file(response))
        result.libraries_io_score = response.get('metadata', {}).get('libraries_io_score', {})
        return result


class PackageManagersFetcher(Fetcher):
    def __init__(self) -> None:
        super().__init__()

    def write_report(self, repo_name: str = 'rep'):
        return super().write_report(repo_name)

    def write_json(self, repo_type=Reports.BLUE.value.repo_name):
        super().write_json(repo_type)

    def get_request(self, url: str) -> requests.Response:
        retries = NO_OF_RETRIES
        response = requests.Response()
        while retries > 0:
            response = requests.get(url)
            if response.status_code not in [HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.BAD_GATEWAY]:
                break
            else:
                retries = retries - 1
                time.sleep(SECONDS_BEFORE_RETRY)
        return response

    def fetch_libraries_io_score(self, package_name: str, site: str) -> Dict[str, Any]:
        libraries_io_api_key = get_environment_var('LIBRARIES_IO_API_KEY')
        package = package_name.replace('/', '%2F')
        url = f"https://libraries.io/api/{site}/{package}/sourcerank?api_key={libraries_io_api_key}"
        response = self.get_request(url)
        if response.status_code == HTTPStatus.NOT_FOUND:
            return {}
        response.raise_for_status()
        return response.json()

    def get_npm_package_names(self) -> Dict[str, Any]:        # npm api (registry.npmjs.org) - query search result
        page = 0
        size = NPM_PAGE_SIZE
        scores_dict = {}

        while True:
            url = self.organization.get_search_url_string(PackagesRegistries.NPM.value, page)
            response = self.get_request(url)
            response.raise_for_status()
            data = response.json()
            package_info = data.get('objects', [])
            # also gets npmjs scores in the form "{package_name}": {package_score}
            scores_dict.update({item.get('package', {}).get('name'): item.get('score', {}) for item in package_info
                                if self.organization.get_search_filter(PackagesRegistries.NPM.value, item)})
            if len(data['objects']) < size:
                break
            page += 1
        return scores_dict

    def fetch_npm_downloads(self, package_name: str) -> Dict[str, Any]:
        url = f'https://api.npmjs.org/downloads/range/{self.start_date}:{self.end_date}/{package_name}'
        response = self.get_request(url)
        if 'not found' in response.text:
            return {}
        response.raise_for_status()
        return response.json()

    def get_crates_package_names(self) -> List[str]:      # crates api (crates/api) - query search result
        package_names = []
        pattern = self.organization.search_includes[PackagesRegistries.CARGO.value.repo_name]
        search_string = f'?q={pattern}'
        while search_string:
            url = PackagesRegistries.CARGO.value.downloads_url + search_string
            response = self.get_request(url)
            response.raise_for_status()
            data = response.json()
            package_info = data.get('crates', [])
            new_package_names = [
                item.get('name') for item in package_info if self.organization.get_search_filter(PackagesRegistries.CARGO.value, item)]
            package_names.extend(new_package_names)
            search_string = data.get('meta', {}).get('next_page', '')
        return package_names

    def fetch_crates_downloads(self, package_name: str):
        url = f"https://crates.io/api/v1/crates/{package_name}/downloads"
        response = self.get_request(url)
        response.raise_for_status()
        data = response.json()
        data['version_downloads'] = [entry for entry in data['version_downloads'] if self.start_date <= entry['date'] <= self.end_date]
        data['meta']['extra_downloads'] = [entry for entry in data['meta']['extra_downloads'] if self.start_date <= entry['date'] <= self.end_date]
        return data

    def get_pypi_package_names(self) -> List[str]:
        package_names = []
        pattern = self.organization.search_includes[PackagesRegistries.PYPI.value.repo_name]
        response = requests.get('https://pypi.org/simple/', headers={"Accept": "application/vnd.pypi.simple.v1+json"})
        response.raise_for_status()
        package_info = response.json().get('projects', [])

        for package in [item for item in package_info if pattern in item.get('name', '')]:
            package_name = package.get('name', '')
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
            if response.status_code == HTTPStatus.NOT_FOUND:
                continue
            response.raise_for_status()
            urls = response.json().get('info', {}).get('project_urls', {})

            if urls and self.organization.get_search_filter(PackagesRegistries.PYPI.value, urls):
                package_names.append(package_name)

        return package_names

    def fetch_pypi_package_score(self, package_name: str) -> Dict[str, Any]:
        score_details = {}
        url = f"https://snyk.io/advisor/python/{package_name}"
        response = self.get_request(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tags: List[Tag] = [item for item in soup.find_all('title')]
            for title_tag in title_tags:
                title_text = title_tag.text
                if 'package health:' in title_text.lower():
                    health_score: int = int(title_text.split(':')[-1].split('/')[0].strip())
                    score_details['final'] = -1 if health_score == '?' else health_score / 100
            score_details['detail'] = {}
            scores_list = soup.find('ul', class_='scores')
            if scores_list and isinstance(scores_list, Tag):
                for li in scores_list.find_all('li'):
                    if isinstance(li, Tag):
                        category_span = li.find('span')
                        status_span = li.find('span', class_='vue--pill__body')

                        if isinstance(category_span, Tag) and isinstance(status_span, Tag):
                            category = category_span.text.strip()
                            status = status_span.text.strip()
                            score_details['detail'][category] = status
        else:
            print(f"Failed to retrieve the details webpage for package {package_name}.")
        return score_details

    def fetch_pypi_downloads(self, package_name: str):
        url = f"https://pypistats.org/api/packages/{package_name}/overall"
        response = self.get_request(url)
        response.raise_for_status()
        data = response.json()
        data['data'] = [entry for entry in data['data']
                        if self.start_date <= entry['date'] <= self.end_date]
        return data

    def get_package(self, item: Dict[str, Any]) -> PackageManagersPackage:
        return PackageManagersPackage.from_generated_file(item)

    @staticmethod
    def from_package_sites(org: Organization, end_date: str) -> 'PackageManagersFetcher':
        result = PackageManagersFetcher()
        result.start_date = str(FormattedDate.from_string(end_date) - DAYS_IN_MONTHLY_REPORT + 1)
        result.end_date = end_date
        result.organization = org

        print("fetching from npm ...")
        packages = result.get_npm_package_names()

        with tqdm(total=len(packages)) as pbar:
            for package_name in packages.keys():
                fetched_downloads = result.fetch_npm_downloads(package_name)
                package_downloads = PackageManagersPackage.from_npm_fetched_data(
                    package_name, Language.JAVASCRIPT.lang_name, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistries.NPM.name)
                package_downloads.site_score = Score.from_dict(packages[package_name])
                result.packages.append(package_downloads)
                pbar.update(1)

        print("fetching from crates ...")
        packages = result.get_crates_package_names()

        with tqdm(total=len(packages)) as pbar:
            for package_name in packages:
                fetched_downloads = result.fetch_crates_downloads(package_name)
                package_downloads = PackageManagersPackage.from_crates_fetched_data(
                    package_name, Language.RUST.lang_name, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistries.CARGO.name)
                result.packages.append(package_downloads)
                pbar.update(1)

        print("fetching from pypi ...")
        packages = result.get_pypi_package_names()

        with tqdm(total=len(packages)) as pbar:
            for package_name in packages:
                fetched_downloads = result.fetch_pypi_downloads(package_name)
                package_downloads = PackageManagersPackage.from_pypi_fetched_data(
                    package_name, Language.PYTHON.lang_name, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistries.PYPI.name)
                package_downloads.site_score = Score.from_dict(result.fetch_pypi_package_score(package_name))
                result.packages.append(package_downloads)
                pbar.update(1)
        return result
