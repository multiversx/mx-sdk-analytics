from datetime import datetime, timedelta
import os
# from pathlib import Path
from typing import Any, Dict, List
from bs4 import BeautifulSoup, Tag
import requests
from tqdm import tqdm

from utils import FormattedDate, Language, PackagesRegistry, Reports
from constants import DAYS_IN_TWO_WEEKS_REPORT, GITHUB_ORGANIZATION, GITHUB_PAGE_SIZE, GITHUB_SEARCH_PREFIX, DATE_FORMAT
from fetcher import DailyActivity, Fetcher, Package, Score


class GithubDailyActivity(DailyActivity):
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
    def from_github_fetched_data(response: Dict[str, Any]) -> 'GithubDailyActivity':
        result = GithubDailyActivity()
        result.date = response.get('timestamp', '1980-01-01')[:10]
        result.downloads = response.get('count', 0)
        result.uniques = response.get('uniques', 0)
        return result

    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'GithubDailyActivity':
        result = super().from_generated_file(response)
        result.uniques = response.get('uniques', 0)
        return result


class GithubPackageObject(Package):
    def __init__(self) -> None:
        super().__init__()
        self.main_page_statistics: Dict[str, Any] = {}
        self.views: List[GithubDailyActivity] = []

    def to_dict(self) -> Dict[str, Any]:
        temp_dict = super().to_dict()
        temp_dict['metadata']['main_page_statistics'] = self.main_page_statistics
        temp_dict['views'] = [item.to_dict() for item in self.views]
        return temp_dict

    # TODO Statistics for clones- uniques, statistics for visitors 
    def create_summary_statistics_from_daily_downloads(self, end_date: str, report_duration=DAYS_IN_TWO_WEEKS_REPORT) -> Dict[str, Any]:
        summary = super().create_summary_statistics_from_daily_downloads(end_date, report_duration)
        
        return summary

    def analyse_package(self):
        main_negatives = ', '.join(f"{key} = 0" for key, value in self.main_page_statistics.items()
                                   if value == 0 and "has" in key)
        score_negatives = ', '.join(f"{key} = {value}" for key, value in self.site_score.detail.items()
                                    if "has" in key and int(value) == 0)
        return main_negatives + (', ' if main_negatives else '') + score_negatives

    # TODO: language from github api 
    @staticmethod
    def from_github_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'GithubPackageObject':
        result = GithubPackageObject()
        raw_downloads = response.get('downloads').get('clones', [])
        raw_views = response.get('visits').get('views', [])
        result.downloads = [GithubDailyActivity.from_github_fetched_data(item) for item in raw_downloads]
        result.views = [GithubDailyActivity.from_github_fetched_data(item) for item in raw_views]
        result.package_name = response.get('package', package)
        result.package_language = lang
        result.package_site = PackagesRegistry.GITHUB.repo_name
        result.no_of_downloads = sum(dd.downloads for dd in result.downloads)
        result.main_page_statistics = response.get('main_page_statistics', {})
        return result

    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'GithubPackageObject':
        result = super().from_generated_file(response)
        result.views = [GithubDailyActivity.from_generated_file(item) for item in response.get('views', [])]
        result.main_page_statistics = response.get('metadata', {}).get('main_page_statistics', {})
        return result

    @property
    def DAILY_ACTIVITY_TYPE(self):
        return GithubDailyActivity


class GithubFetcherObject(Fetcher):
    def __init__(self) -> None:
        super().__init__()

    def write_report(self):
        super().write_report("rep")

    def write_json(self):
        super().write_json(repo_type=Reports.GREEN.value)

    def get_github_package_names(self, pattern: str) -> Dict[str, Any]:        # github api - query search result
        def build_package_main_page_score(item: Dict[str, Any]) -> Dict[str, Any]:
            return {
                'stargazers_count': item.get('stargazers_count', 0),
                'forks_count': item.get('forks_count', 0),
                'watchers_count': item.get('watchers_count', 0),
                'has_issues': item.get('has_issues', 0),
                'has_projects': item.get('has_projects', 0),
                'has_downloads': item.get('has_downloads', 0),
                'has_wiki': item.get('has_wiki', 0),
                'has_pages': item.get('has_pages', 0),
                'has_discussions': item.get('has_discussions', 0),
            }
        page = 0
        size = GITHUB_PAGE_SIZE
        scores_dict = {}
        owner = GITHUB_ORGANIZATION
        while True:
            url = f"https://api.github.com/search/repositories?q={pattern}+in:name+user:{owner}&per_page={size}&page={page}&sort=stars&order=desc"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            package_info = data.get('items', [])
            # also gets main page scores in the form "{package_name}": {package_score}
            scores_dict.update({item.get('name'): build_package_main_page_score(item) for item in package_info})
            if len(data['items']) < size:
                break
            page += 1
        return scores_dict

    def fetch_github_downloads(self, package_name: str):
        bearer_token = os.environ.get("MX_GITHUB_TOKEN")
        owner = GITHUB_ORGANIZATION
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = f"https://api.github.com/repos/{owner}/{package_name}/traffic/clones"
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            print(package_name)
        else:
            response.raise_for_status()
        return response.json()

    def fetch_github_visits(self, package_name: str):
        bearer_token = os.environ.get("MX_GITHUB_TOKEN")
        owner = GITHUB_ORGANIZATION
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = f"https://api.github.com/repos/{owner}/{package_name}/traffic/views"
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            print(package_name)
        else:
            response.raise_for_status()
        return response.json()

    def fetch_github_package_community_score(self, package_name: str) -> Dict[str, Any]:
        score = {}
        bearer_token = os.environ.get("MX_GITHUB_TOKEN")
        owner = GITHUB_ORGANIZATION
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = f"https://api.github.com/repos/{owner}/{package_name}/community/profile"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        health_score: int = data.get('health_percentage', 0)
        score['final'] = health_score / 100
        score['detail'] = {}
        for item in ['description', 'documentation']:
            score['detail'][f"has_{item}"] = 0 if data.get(item, '') is None else 1
        for item in ['code_of_conduct', 'contributing', 'issue_template', 'pull_request_template', 'license', 'readme']:
            score['detail'][f"has_{item}"] = 0 if data.get('files', {}).get(item, '') is None else 1
        timestamp = data.get('updated_at', '')
        format = "%Y-%m-%dT%H:%M:%SZ"
        score['detail']['updated_at'] = str(FormattedDate.from_format(timestamp, format)) if timestamp else ''
        score['detail']['content_reports_enabled'] = 1 if data.get('content_reports_enabled', '') else 0
        return score

    # TODO language implementation
    @staticmethod
    def from_package_sites(end_date: str) -> 'GithubFetcherObject':
        result = GithubFetcherObject()
        result.start_date = str(FormattedDate.from_string(end_date) - DAYS_IN_TWO_WEEKS_REPORT + 1)
        result.end_date = end_date

        print("fetching from github ...")
        packages = result.get_github_package_names(GITHUB_SEARCH_PREFIX)
        with tqdm(total=len(packages)) as pbar:
            for package_name in packages.keys():
                fetched_downloads = result.fetch_github_downloads(package_name)
                fetched_visits = result.fetch_github_visits(package_name)
                fetched = {"downloads": fetched_downloads, "visits": fetched_visits}
                package_downloads = GithubPackageObject.from_github_fetched_data(
                    package_name, Language.JAVASCRIPT.value, fetched)
                package_downloads.main_page_statistics = packages[package_name]
                package_downloads.site_score = Score.from_dict(result.fetch_github_package_community_score(package_name))
                result.downloads.append(package_downloads)
                pbar.update(1)
        return result

    @staticmethod
    def get_github_rate_limit(token: str):
        rate_limit_url = "https://api.github.com/rate_limit"
        response = requests.get(rate_limit_url, headers={"Authorization": f"token {token}"})
        print(response.json())
        reset_time = int(response.headers.get("X-RateLimit-Reset"))
        remaining = int(response.headers.get("X-RateLimit-Remaining"))
        print(f"Rate limit will reset at {reset_time}. You have {remaining} requests left.")

    @property
    def PACKAGE_CLASS(self):
        return GithubPackageObject
