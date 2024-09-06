import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

from constants import DATE_FORMAT, DAYS_IN_MONTHLY_REPORT, DAYS_IN_WEEK
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
    def from_dict(info: Dict[str, Any]) -> 'Score':
        response = Score()
        response.final = info.get('final', 0)
        response.detail = info.get('detail', {})
        return response


class DailyActivity:
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
    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'DailyActivity':
        result = cls()
        result.date = response.get('date', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result


class Package:
    def __init__(self) -> None:
        self.package_name = ''
        self.package_language = ''
        self.package_site = ''
        self.downloads: List[DailyActivity] = []
        self.no_of_downloads = 0
        self.libraries_io_score: Dict[str, Any] = {}
        self.site_score = Score()

    def __str__(self):
        print_str = f"PACKAGE = {self.package_name} - language = {self.package_language} - site = {self.package_site} - downloads = {self.no_of_downloads}\n"
        print_str += "\n".join(str(item) for item in self.downloads)
        print_str += "\n"
        return print_str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "section_name": self.package_site,
                "package_name": self.package_name,
                "language": self.package_language,
                "no_of_downloads": self.no_of_downloads,
                "libraries_io_score": self.libraries_io_score,
                "site_score": self.site_score.to_dict()
            },
            "downloads": [item.to_dict() for item in self.downloads]
        }

    def create_summary_statistics_from_daily_downloads(self, end_date: str, report_duration: int = DAYS_IN_MONTHLY_REPORT) -> Dict[str, Any]:
        last_month_downloads = sum(dd.downloads for dd in self.downloads)
        avg_daily_downloads = last_month_downloads / report_duration
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
    
    @property
    def DAILY_ACTIVITY_TYPE(self):
        return DailyActivity
    
    @classmethod
    def from_generated_file(cls, response: Dict[str, Any]) -> 'Package':
        result = cls()
        raw_downloads = response.get('downloads', [])
        result.downloads = [result.DAILY_ACTIVITY_TYPE.from_generated_file(item) for item in raw_downloads]
        meta: Dict[str, Any] = response.get('metadata', '')
        result.package_name = meta.get('package_name', '')
        result.package_site = meta.get('section_name', '')
        result.package_language = meta.get('language', '')
        result.no_of_downloads = meta.get('no_of_downloads', '')
        result.libraries_io_score = meta.get('libraries_io_score', {})
        result.site_score = Score.from_dict(meta.get('site_score', {}))
        return result


class Fetcher:
    def __init__(self) -> None:
        self.start_date = ''
        self.end_date = ''
        self.downloads: List[Package] = []
        self.rep_folder = os.environ.get("JSON_FOLDER")

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

    def write_report(self, repo_name: str = 'log'):
        print("writting report ...")
        report_name = Path(self.rep_folder) / f"{repo_name}{self.end_date}.txt"
        report_name.write_text(str(self))

    def write_json(self, repo_type: str):
        print("writting json ...")
        report_name = Path(self.rep_folder) / f"{repo_type}{self.end_date}.json"
        report_name.write_text(json.dumps(self.to_dict(), indent=4))
    
    def fetch_libraries_io_score(self, package_name: str, site: str) -> Dict[str, Any]:
        libraries_io_api_key = os.environ.get('LIBRARIES_IO_API_KEY')
        package = package_name.replace('/', '%2F')
        url = f"https://libraries.io/api/{site}/{package}/sourcerank?api_key={libraries_io_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    @classmethod
    def from_generated_file(cls, file_name: str) -> 'Fetcher':
        with open(file_name, 'r') as file:
            json_data: Dict[str, Any] = json.load(file)
        result = cls()
        meta: Dict[str, Any] = json_data.get('metadata')
        result.start_date = meta.get('start_date', '')
        result.end_date = meta.get('end_date', '')
        result.downloads = [result.PACKAGE_CLASS.from_generated_file(item) for item in json_data.get('records', [])]
        return result

    @property
    def PACKAGE_CLASS(self):    
        return Package      #Overwritten in inherited classes

'''
def sum_activity_for_report_duration(activity_list: List[DailyActivity]):
    return sum(dd.downloads for dd in activity_list)
def sum_activity_for_seven_days(activity_list: List[DailyActivity], end_date:str):
    seven_days_before = (datetime.strptime(end_date, DATE_FORMAT).date() - timedelta(DAYS_IN_WEEK - 1)).strftime(DATE_FORMAT)
    return sum(dd.downloads for dd in [item for item in activity_list if item.date >= seven_days_before])
'''