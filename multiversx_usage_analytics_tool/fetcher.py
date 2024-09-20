import json
import os
from pathlib import Path
from typing import Any, Dict, List

from constants import DAYS_IN_WEEK, DEFAULT_DATE
from ecosystem import Organization
from utils import FormattedDate

'''
in order to allow calculations of scores in future implementations, the score must be a dictionary of individual composite scores
the general score is calculated as a weighted means of composite scores, which in turn will be weighted means of individual scores.

NPM: final_score = weightedMean([[quality, 6],[popularity, 7],[maintenance, 7]]);
NPM: quality = weightedMean([[carefulness, 7],[tests, 7],[health, 4],[branding, 2]]);
NPM: maintanance = weightedMean([[releasesFrequency, 2],[commitsFrequency, 1],[openIssues, 1],[issuesDistribution, 2]]);
NPM: popularity = weightedMean([[communityInterest, 2],[downloadsCount, 2],[downloadsAcceleration, 1],// [scores.dependentsCount, 2]]);
PYPI: health_score = weightedMean([[security, 6],[popularity, 6],[maintanance, 4],[community, 4]]);
'''


class Score:
    def __init__(self) -> None:
        self.final: float = 0
        self.details: Dict[str, Any] = {}

    def __repr__(self) -> str:
        return ', '.join(f"{key} = {float(value):.2f}" if isinstance(value, (float, int)) else f"{key} = {value}" for key, value in self.details.items())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'final': self.final,
            'detail': self.details
        }

    @staticmethod
    def from_dict(info: Dict[str, Any]) -> 'Score':
        if not info:
            return Score()
        response = Score()
        response.final = info.get('final', 0)
        response.details = info.get('detail', {})
        return response


class DailyActivity:
    def __init__(self, date: str = DEFAULT_DATE, count: int = 0) -> None:
        self.date = date
        self.downloads = count

    def __str__(self) -> str:
        return f"{self.date} - {self.downloads} downloads"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date,
            'downloads': self.downloads
        }

    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'DailyActivity':
        result = cls()
        result.date = response.get('date', DEFAULT_DATE)
        result.downloads = response.get('downloads', 0)
        return result


class Package:
    def __init__(self) -> None:
        self.package_name = ''
        self.package_language = ''
        self.package_site = ''
        self.downloads: List[DailyActivity] = []
        self.no_of_downloads = 0
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
                'site_score': self.site_score.to_dict()
            },
            'downloads': [item.to_dict() for item in self.downloads]
        }

    def create_summary_statistics_from_daily_downloads(self, end_date: str, report_duration: int) -> Dict[str, Any]:
        summary_dict = self.calculate_activity_statistics('downloads', self.downloads, end_date, report_duration)
        summary_dict['site_score'] = f"{self.site_score.final:.2f}"
        summary_dict['site_score_details'] = repr(self.site_score)
        return summary_dict

    def calculate_activity_statistics(self, name: str, activity: List[DailyActivity], end_date: str, report_duration: int) -> Dict[str, Any]:
        last_month_downloads = sum(dd.downloads for dd in activity)
        avg_daily_downloads = last_month_downloads / report_duration
        seven_days_before = str(FormattedDate.from_string(end_date) - DAYS_IN_WEEK + 1)
        last_week_downloads = sum(dd.downloads for dd in [item for item in activity if item.date >= seven_days_before])
        return {
            f"{name}_total": last_month_downloads,
            f"{name}_last_week": last_week_downloads,
            f"avg_daily_{name}": avg_daily_downloads,
        }

    def get_daily_activity(self, item: Dict[str, Any]):
        return DailyActivity.from_generated_file(item)

    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'Package':
        result = cls()
        raw_downloads = response.get('downloads', [])
        result.downloads = [result.get_daily_activity(item) for item in raw_downloads]
        meta: Dict[str, Any] = response.get('metadata', '')
        result.package_name = meta.get('package_name', '')
        result.package_site = meta.get('section_name', '')
        result.package_language = meta.get('language', '')
        result.no_of_downloads = meta.get('no_of_downloads', '')
        result.site_score = Score.from_dict(meta.get('site_score', {}))
        return result


class Fetcher:
    def __init__(self) -> None:
        self.start_date = ''
        self.end_date = ''
        self.packages: List[Package] = []
        self.rep_folder = os.environ.get("JSON_FOLDER")
        self.organization = Organization()

    def __str__(self):
        print_str = f"DOWNLOADS REPORT ({self.start_date} - {self.end_date})\n\n"
        print_str += "\n".join(str(item) for item in self.packages)
        print_str += "\n"
        return print_str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metadata': {
                'organization': self.organization.name,
                'start_date': self.start_date,
                'end_date': self.end_date,
            },
            'records': [item.to_dict() for item in self.packages]
        }

    def write_report(self, repo_name: str = 'log'):
        print("writting report ...")
        report_name = Path(self.rep_folder) / f"{repo_name}{self.end_date}.txt"  # type: ignore
        report_name.write_text(str(self))

    def write_json(self, repo_type: str):
        print("writting json ...")
        report_name = Path(self.rep_folder) / f"{repo_type}{self.end_date}.json"  # type: ignore
        report_name.write_text(json.dumps(self.to_dict(), indent=4))

    def get_package(self, item: Dict[str, Any]) -> Package:
        return Package.from_generated_file(item)

    @classmethod
    def from_generated_file(cls, file_name: str, organization: Organization) -> 'Fetcher':
        with open(file_name, 'r') as file:
            json_data: Dict[str, Any] = json.load(file)
        result = cls()
        organization_data: Dict[str, Any] = json_data.get(organization.name, {})

        meta: Dict[str, Any] = organization_data.get('metadata', {})
        result.start_date = meta.get('start_date', '')
        result.end_date = meta.get('end_date', '')
        result.packages = [result.get_package(item) for item in organization_data.get('records', [])]
        return result
