from datetime import datetime, timedelta
from functools import reduce
import json
import os
# from pathlib import Path
from typing import Any, Dict, List
from bs4 import BeautifulSoup, Tag
import requests
from tqdm import tqdm

from utils import Language, PackagesRegistry
from constants import DAYS_IN_TWO_WEEKS_REPORT, GITHUB_SEARCH_PREFIX, DATE_FORMAT
from fetcher import DailyDownloads, FetcherObject, PackageObject, ScoreObject


class GithubDailyDownloads(DailyDownloads):
    def __init__(self) -> None:
        super().__init__()
        self.uniques = 0

    def __str__(self) -> str:
        return super().__str__() + f", {self.uniques} uniques"

    def to_dict(self) -> Dict[str, Any]:
        temp_dict = super().to_dict()
        temp_dict['uniques'] = self.uniques
        return temp_dict

    @staticmethod
    def from_github_fetched_data(response: Dict[str, Any]) -> 'GithubDailyDownloads':
        result = GithubDailyDownloads()
        result.date = response.get('timestamp', '1980-01-01')[:10]
        result.downloads = response.get('count', 0)
        result.uniques = response.get('uniques', 0)
        return result

    @classmethod
    def from_json_file(cls, response: Dict[str, Any]) -> 'GithubDailyDownloads':
        result = super().from_json_file(response)
        result.uniques = response.get('uniques', 0)
        return result


class GithubPackageObject(PackageObject):
    def __init__(self) -> None:
        super().__init__()
        self.views: List[DailyDownloads] = []

    def to_dict(self) -> Dict[str, Any]:
        temp_dict = super().to_dict()
        temp_dict['views'] = self.views
        return temp_dict

    @staticmethod
    def from_github_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'GithubPackageObject':
        result = GithubPackageObject()
        raw_downloads = response.get('downloads', [])
        raw_views = response.get('views', [])
        result.downloads = [GithubDailyDownloads.from_github_fetched_data(
            item) for item in raw_downloads]
        result.views = [GithubDailyDownloads.from_github_fetched_data(
            item) for item in raw_views]
        result.package_name = response.get('package', package)
        result.package_language = lang
        result.package_site = PackagesRegistry.GITHUB.repo_name
        result.no_of_downloads = reduce(
            lambda acc, dd: acc + dd.downloads, result.downloads, 0)
        return result

    @classmethod
    def from_json_file(cls, response: Dict[str, Any]) -> 'GithubPackageObject':
        result = super().from_json_file(response)
        result.views = response.get('views', [])
        return result


class GithubFetcherObject(FetcherObject):
    def write_report(self):
        super().write_report("rep")

    def write_json(self):
        super().write_json(repo_type="green")
# https://api.github.com/search/repositories?q=sdk+in:name+user:multiversx&sort=stars&order=desc

    def get_github_package_names(self, pattern: str) -> Dict[str, Any]:        # npm api (registry.npmjs.org) - query search result
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

    def fetch_github_downloads(self, package_name: str):
        url = f"https://api.npmjs.org/downloads/range/{self.start_date}:{self.end_date}/{package_name}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def fetch_github_package_score(self, package_name: str) -> json:
        score_details = {}
        url = f"https://snyk.io/advisor/python/{package_name}"
        response = requests.get(url)
        response.raise_for_status()

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
        return score_details

    @staticmethod
    def from_package_sites(date: str) -> 'GithubFetcherObject':
        result = GithubFetcherObject()
        end_date = datetime.strptime(date, DATE_FORMAT)
        start_date = end_date - timedelta(DAYS_IN_TWO_WEEKS_REPORT - 1)
        result.start_date = start_date.strftime(DATE_FORMAT)
        result.end_date = date

        print("fetching from github ...")
        packages = result.get_github_package_names(GITHUB_SEARCH_PREFIX)
        with tqdm(total=len(packages)) as pbar:
            for package_name in packages.keys():
                fetched_downloads = result.fetch_github_downloads(package_name)
                package_downloads = GithubPackageObject.from_github_fetched_data(
                    package_name, Language.JAVASCRIPT.value, fetched_downloads)
                package_downloads.libraries_io_score = result.fetch_libraries_io_score(package_name, PackagesRegistry.NPM.name)
                package_downloads.site_score = ScoreObject.from_json(packages[package_name])
                result.downloads.append(package_downloads)
                pbar.update(1)
        return result
