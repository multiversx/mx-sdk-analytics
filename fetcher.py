from datetime import datetime, timedelta
from functools import reduce
import json
import os
from pathlib import Path
from typing import Any, Dict, List
import requests
from constants import DAYS_IN_MONTHLY_REPORT, DAYS_IN_WEEK, DATE_FORMAT

# in order to permit calculations of scores in future implementations, the score must be a dictionary of individual composit scores
# the general score is calculated as a weighted means of composit scores, which in turn will be weighted means of individual scores.
#
# NPM: final_score = weightedMean([[quality, 6],[popularity, 7],[maintenance, 7]]);
# NPM: quality = weightedMean([[carefulness, 7],[tests, 7],[health, 4],[branding, 2]]);
# NPM: maintanance = weightedMean([[releasesFrequency, 2],[commitsFrequency, 1],[openIssues, 1],[issuesDistribution, 2]]);
# NPM: popularity = weightedMean([[communityInterest, 2],[downloadsCount, 2],[downloadsAcceleration, 1],// [scores.dependentsCount, 2]]);
# PYPI: health_score = weightedMean([[security, 6],[popularity, 6],[maintanance, 4],[community, 4]]);


class ScoreObject:
    def __init__(self) -> None:
        self.final: float = 0
        self.detail: Dict[str, Any] = {}

    def __repr__(self) -> str:
        return ", ".join(f"{key} = {float(value):.2f}" if isinstance(value, (float, int)) else f"{key} = {value}" for key, value in self.detail.items())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final": self.final,
            "detail": self.detail
        }

    @staticmethod
    def from_json(info: Dict[str, Any]) -> 'ScoreObject':
        response = ScoreObject()
        response.final = info.get("final", 0)
        response.detail = info.get("detail", {})
        return response


class DailyDownloads:
    def __init__(self) -> None:
        self.date = "1980-01-01"
        self.downloads = 0

    def __str__(self) -> str:
        return f"{self.date} - {self.downloads} downloads"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "downloads": self.downloads
        }

    @classmethod
    def from_json_file(cls, response: Dict[str, Any]) -> 'DailyDownloads':
        result = cls()
        result.date = response.get('date', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result


class PackageObject:
    def __init__(self) -> None:
        self.package_name = ''
        self.package_language = ''
        self.package_site = ''
        self.downloads: List[DailyDownloads] = []
        self.no_of_downloads = 0
        self.libraries_io_score: json = {}
        self.site_score = ScoreObject()

    def __str__(self):
        print_str = f"PACKAGE = {self.package_name} - language = {self.package_language} - site = {
            self.package_site} - downloads = {self.no_of_downloads}\n"
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

    def create_summary_of_monthly_statistics_from_daily_downloads(self, end_date: str) -> Dict[str, Any]:
        last_month_downloads = reduce(lambda acc, dd: acc + dd.downloads, self.downloads, 0)
        avg_daily_downloads = last_month_downloads / DAYS_IN_MONTHLY_REPORT
        seven_days_before = (datetime.strptime(end_date, DATE_FORMAT).date() - timedelta(DAYS_IN_WEEK - 1)).strftime(DATE_FORMAT)
        last_week_downloads = reduce(lambda acc, dd: acc + dd.downloads, [item for item in self.downloads if item.date >= seven_days_before], 0)
        return {
            "last_month_downloads": last_month_downloads,
            "last_week_downloads": last_week_downloads,
            "avg_daily_downloads": avg_daily_downloads,
            "libraries_io_score": reduce(lambda acc, value: acc + value, self.libraries_io_score.values(), 0),
            "libraries_io_negatives": self.analyse_libraries_io_score(),
            "site_score": f"{self.site_score.final:.2f}",
            "site_score_details": repr(self.site_score)
        }

    def analyse_libraries_io_score(self):
        negatives = ", ".join(f"{key} = {value}" for key, value in self.libraries_io_score.items()
                              if value < 0 or value == 0 and "present" in key)
        return negatives

    @classmethod
    def from_json_file(cls, response: Dict[str, Any]) -> 'PackageObject':
        result = cls()
        raw_downloads = response.get('downloads', [])
        result.downloads = [DailyDownloads.from_json_file(
            item) for item in raw_downloads]
        meta: Dict[str, Any] = response.get('metadata', '')
        result.package_name = meta.get('package_name', '')
        result.package_site = meta.get('section_name', '')
        result.package_language = meta.get('language', '')
        result.no_of_downloads = meta.get('no_of_downloads', '')
        result.libraries_io_score = meta.get('libraries_io_score', {})
        result.site_score = ScoreObject.from_json(meta.get('site_score', {}))
        return result


class FetcherObject:
    def __init__(self) -> None:
        self.start_date = ''
        self.end_date = ''
        self.downloads: List[PackageObject] = []
        self.rep_folder = os.environ.get("JSON_FOLDER")

    def __str__(self):
        print_str = f"DOWNLOADS REPORT ({
            self.start_date} - {self.end_date})\n\n"
        print_str += "\n".join(str(item) for item in self.downloads)
        print_str += "\n"
        return print_str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "report_type": "blue",
                "start_date": self.start_date,
                "end_date": self.end_date,
            },
            "records": [item.to_dict() for item in self.downloads]
        }

    def write_report(self, repo_name: str = 'log'):
        print("writting report ...")
        report_name = Path(self.rep_folder) / f"{repo_name}{self.end_date}.txt"
        report_name.write_text(str(self))

    def write_json(self, repo_type: str):
        print("writting json ...")
        report_name = Path(self.rep_folder) / f"{repo_type}{self.end_date}.json"
        report_name.write_text(json.dumps(self.to_dict(), indent=4))

    def fetch_libraries_io_score(self, package_name: str, site: str) -> json:
        libraries_io_api_key = os.environ.get("LIBRARIES_IO_API_KEY")
        package = package_name.replace('/', '%2F')
        url = f"https://libraries.io/api/{site}/{package}/sourcerank?api_key={libraries_io_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def from_json_file(file_name: str) -> 'FetcherObject':
        with open(file_name, 'r') as file:
            json_data: Dict[str, Any] = json.load(file)
        result = FetcherObject()
        meta: Dict[str, Any] = json_data.get('metadata')
        result.start_date = meta.get('start_date', '')
        result.end_date = meta.get('end_date', '')
        result.downloads = [PackageObject.from_json_file(
            item) for item in json_data.get('records', [])]
        return result
