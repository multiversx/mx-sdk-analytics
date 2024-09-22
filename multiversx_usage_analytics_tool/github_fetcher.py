import os
from http import HTTPStatus
from typing import Any, Dict, List, cast

import requests
from tqdm import tqdm

from multiversx_usage_analytics_tool.constants import (
    DAYS_IN_TWO_WEEKS_REPORT, DEFAULT_DATE, GITHUB_OWN_ORGANIZATION,
    GITHUB_PAGE_SIZE)
from multiversx_usage_analytics_tool.ecosystem import (Organization,
                                                       Organizations)
from multiversx_usage_analytics_tool.fetcher import (DailyActivity, Fetcher,
                                                     Package, Score)
from multiversx_usage_analytics_tool.utils import (FormattedDate, Language,
                                                   PackagesRegistry, Reports)


class GithubDailyActivity(DailyActivity):
    def __init__(self, date: str = DEFAULT_DATE, count: int = 0, uniques: int = 0) -> None:
        super().__init__(date, count)
        self.uniques = uniques

    def __str__(self) -> str:
        return super().__str__() + f", {self.uniques} uniques"

    def to_dict(self) -> Dict[str, Any]:
        temp_dict = super().to_dict()
        temp_dict['uniques'] = self.uniques
        return temp_dict

    @staticmethod
    def from_github_fetched_data(response: Dict[str, Any]) -> 'GithubDailyActivity':
        result = GithubDailyActivity()
        format = "%Y-%m-%dT%H:%M:%SZ"
        default_time_in_github_format = FormattedDate.from_string(DEFAULT_DATE).to_format(format)
        result.date = str(FormattedDate.from_format(response.get('timestamp', default_time_in_github_format), format))
        result.downloads = response.get('count', 0)
        result.uniques = response.get('uniques', 0)
        return result

    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'GithubDailyActivity':
        result = cast(GithubDailyActivity, super().from_generated_file(response))
        result.uniques = response.get('uniques', 0)
        return result


class GithubPackage(Package):
    def __init__(self) -> None:
        super().__init__()
        self.main_page_statistics: Dict[str, Any] = {}
        self.views: List[GithubDailyActivity] = []

    def to_dict(self) -> Dict[str, Any]:
        temp_dict = super().to_dict()
        temp_dict['metadata']['main_page_statistics'] = self.main_page_statistics
        temp_dict['views'] = [item.to_dict() for item in self.views]
        return temp_dict

    def create_summary_statistics_from_daily_downloads(self, end_date: str, report_duration=DAYS_IN_TWO_WEEKS_REPORT) -> Dict[str, Any]:
        temp_summary: Dict[str, Any] = {}
        # clones - count, score etc.
        summary: Dict[str, Any] = super().create_summary_statistics_from_daily_downloads(end_date, report_duration)
        # clones - uniques
        temp_list = [DailyActivity(item.date, item.uniques) for item in self.downloads]  # type: ignore
        temp_summary = self.calculate_activity_statistics('downloaders', temp_list, end_date, report_duration)
        summary.update(temp_summary)
        # visits - count
        temp_summary = self.calculate_activity_statistics('visits', self.views, end_date, report_duration)  # type: ignore
        summary.update(temp_summary)
        # visits - uniques
        temp_list = [DailyActivity(item.date, item.uniques) for item in self.views]
        temp_summary = self.calculate_activity_statistics('visitors', temp_list, end_date, report_duration)
        summary.update(temp_summary)
        return summary

    def analyse_package(self) -> str:
        main_negatives = ', '.join(f"{key} = 0" for key, value in self.main_page_statistics.items()
                                   if value == 0 and "has" in key)
        score_negatives = ', '.join(f"{key} = {value}" for key, value in self.site_score.details.items()
                                    if "has" in key and int(value) == 0)
        return main_negatives + (', ' if main_negatives else '') + score_negatives

    def get_daily_activity(self, item: Dict[str, Any]) -> GithubDailyActivity:         # override
        return GithubDailyActivity.from_generated_file(item)

    @staticmethod
    def from_github_fetched_data(package: str, lang: str, response: Dict[str, Any]) -> 'GithubPackage':
        result = GithubPackage()
        raw_downloads = response.get('downloads', {}).get('clones', [])
        raw_views = response.get('visits', {}).get('views', [])
        result.downloads = [GithubDailyActivity.from_github_fetched_data(item) for item in raw_downloads]
        result.views = [GithubDailyActivity.from_github_fetched_data(item) for item in raw_views]
        result.package_name = response.get('package', package)
        result.package_language = lang
        result.package_site = PackagesRegistry.GITHUB.repo_name
        result.no_of_downloads = sum(dd.downloads for dd in result.downloads)
        result.main_page_statistics = response.get('main_page_statistics', {})
        return result

    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'GithubPackage':
        result = cast(GithubPackage, super().from_generated_file(response))
        result.views = [result.get_daily_activity(item) for item in response.get('views', [])]
        result.main_page_statistics = response.get('metadata', {}).get('main_page_statistics', {})
        return result


class GithubFetcher(Fetcher):
    def __init__(self) -> None:
        super().__init__()
        self.forbidden_traffic_access_packages = []

    def write_report(self, repo_name: str = 'rep'):
        return super().write_report(repo_name)

    def write_json(self, repo_type=Reports.GREEN.value) -> None:
        super().write_json(repo_type)

    def get_package(self, item: Dict[str, Any]) -> GithubPackage:
        return GithubPackage.from_generated_file(item)

    def build_package_main_page_score(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'language': item.get('language', ''),
            'stargazers_count': item.get('stargazers_count', 0),
            'forks_count': item.get('forks_count', 0),
            'watchers_count': item.get('watchers_count', 0),
            'has_issues': item.get('has_issues', 0),
            'has_projects': item.get('has_projects', 0),
            'has_downloads': item.get('has_downloads', 0),
            'has_wiki': item.get('has_wiki', 0),
            'has_pages': item.get('has_pages', 0),
            'has_discussions': item.get('has_discussions', 0),
            'is_forked': item.get('fork', False)
        }

    def _get_github_authorization_header(self) -> Dict[str, Any]:
        bearer_token = os.environ.get("MX_GITHUB_TOKEN")
        return {"Authorization": f"Bearer {bearer_token}"}

    def get_github_package_names(self) -> Dict[str, Any]:        # github api - query search result
        page = 0
        size = GITHUB_PAGE_SIZE
        scores_dict = {}

        while True:
            url = self.organization.get_search_url_string(PackagesRegistry.GITHUB, page)
            response = requests.get(url, headers=self._get_github_authorization_header())
            response.raise_for_status()
            data = response.json()
            package_info = data.get('items', [])

            # also gets main page scores in the form "{package_name}": {package_score}
            scores_dict.update({item.get('full_name'): self.build_package_main_page_score(item) for item in package_info})
            if len(data['items']) < size:
                break
            page += 1
        return scores_dict

    def fetch_github_downloads(self, package_name: str) -> Dict[str, Any]:
        url = f'{self.organization.get_downloads_url_string(PackagesRegistry.GITHUB, package_name)}/clones'
        response = requests.get(url, headers=self._get_github_authorization_header())

        if response.status_code == HTTPStatus.FORBIDDEN:
            self.forbidden_traffic_access_packages.append(package_name)
        else:
            response.raise_for_status()
        return response.json()

    def fetch_github_visits(self, package_name: str) -> Dict[str, Any]:
        url = f'{self.organization.get_downloads_url_string(PackagesRegistry.GITHUB, package_name)}/views'
        response = requests.get(url, headers=self._get_github_authorization_header())

        if response.status_code == HTTPStatus.FORBIDDEN:
            pass    # already logged from downloads
        else:
            response.raise_for_status()
        return response.json()

    def fetch_github_package_community_score(self, package_name: str) -> Dict[str, Any]:
        score = {}
        url = f"https://api.github.com/repos/{package_name}/community/profile"
        response = requests.get(url, headers=self._get_github_authorization_header())
        if response.status_code == HTTPStatus.NOT_FOUND:
            print(f'{package_name} - community_profile not found')
        else:
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

    def github_package_language(self, package_name: str, language: str) -> Language:
        packet_language = next((lang for lang in Language if any("-" + suffix in package_name for suffix in lang.suffixes)), None)

        if not packet_language:
            if language == 'TypeScript':
                return Language.JAVASCRIPT
            else:
                return next((lang for lang in Language if language and language.lower() == lang.lang_name.lower()), Language.UNKNOWN)
        else:
            return packet_language

    @staticmethod
    def from_package_sites(organization: Organization, end_date: str) -> 'GithubFetcher':
        result = GithubFetcher()
        result.start_date = str(FormattedDate.from_string(end_date) - DAYS_IN_TWO_WEEKS_REPORT + 1)
        result.end_date = end_date
        result.organization = organization
        my_organization = Organizations[GITHUB_OWN_ORGANIZATION].value

        print("fetching from github ...")
        packages = result.get_github_package_names()

        with tqdm(total=len(packages)) as pbar:
            for package_name in packages.keys():
                fetched_downloads = result.fetch_github_downloads(package_name) if organization == my_organization else {}
                fetched_visits = result.fetch_github_visits(package_name) if organization == my_organization else {}
                fetched = {"downloads": fetched_downloads, "visits": fetched_visits}
                packet_language = result.github_package_language(package_name, packages[package_name]['language'])

                package_downloads = GithubPackage.from_github_fetched_data(
                    package_name, packet_language.lang_name, fetched)
                package_downloads.main_page_statistics = packages[package_name]
                if not package_downloads.main_page_statistics['is_forked']:
                    package_downloads.site_score = Score.from_dict(result.fetch_github_package_community_score(package_name))
                result.packages.append(package_downloads)
                pbar.update(1)

        if organization == my_organization and result.forbidden_traffic_access_packages:
            print()
            print("Packages that didn't allow access to traffic information: ")
            for package_name in result.forbidden_traffic_access_packages:
                print(package_name)
            print()
        return result
