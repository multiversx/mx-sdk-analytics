import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from constants import DATE_FORMAT


class Reports (Enum):
    BLUE = 'blue'
    GREEN = 'green'


class Language(Enum):
    JAVASCRIPT = ('Javascript', ['js', 'nestjs'])
    RUST = ('Rust', ['rs', 'rust'])
    PYTHON = ('Python', ['py'])
    CSHARP = ('C#', ['csharp'])
    C = ('C/C++', ['clang', 'cpp'])
    GO = ('Go', ['go'])
    PHP = ('PHP', ['php'])
    JAVA = ('Java', ['java'])
    KOTLIN = ('Kotlin', ['kotlin'])
    UNKNOWN = ('Unknown', ['unknown'])

    def __init__(self, lang_name: str, suffixes: list[str]):
        self.lang_name = lang_name
        self.suffixes = suffixes


class PackagesRegistry(Enum):
    NPM = ('npmjs', 'https://registry.npmjs.org/-/v1/search', 'https://api.npmjs.org/downloads/range', [Reports.BLUE])
    CARGO = ('crates.io', 'https://crates.io/api/v1/crates', 'https://crates.io/api/v1/crates', [Reports.BLUE])
    PYPI = ('pypi', 'https://pypi.org/search', 'https://pypistats.org/api/packages', [Reports.BLUE])
    GITHUB = ('github', 'https://api.github.com/search/repositories', 'https://api.github.com/repos', [Reports.GREEN])

    def __init__(self, repo_name: str, search_url: str, downloads_url: str, reports: list[Reports]):
        self.repo_name = repo_name
        self.search_url = search_url
        self.downloads_url = downloads_url
        self.reports = reports


class FormattedDate:
    def __init__(self, date: datetime) -> None:
        self.date = date

    @classmethod
    def from_string(cls, date_string: str) -> 'FormattedDate':
        try:
            parsed_date = datetime.strptime(date_string, DATE_FORMAT)
            return cls(parsed_date)
        except ValueError:
            raise ValueError(f"Date must be in {DATE_FORMAT} format: {date_string}")

    def __str__(self):
        return self.date.strftime(DATE_FORMAT)

    def __add__(self, added_days: int) -> 'FormattedDate':
        result_date = self.date + timedelta(added_days)
        return FormattedDate(result_date)

    def __sub__(self, substracted_days: int) -> 'FormattedDate':
        result_date = self.date - timedelta(substracted_days)
        return FormattedDate(result_date)

    def __lt__(self, a_date: 'FormattedDate') -> bool:
        return self.date.__lt__(a_date.date)

    def __gt__(self, a_date: 'FormattedDate') -> bool:
        return self.date.__gt__(a_date.date)

    def get_week_and_day_string(self) -> str:
        return f"week= {self.date.isocalendar().week}, weekday= {self.date.isocalendar().weekday}"

    def days_from(self, other: 'FormattedDate') -> int:
        return (self.date - other.date).days

    @staticmethod
    def get_current_week() -> int:
        return datetime.now().isocalendar().week

    @staticmethod
    def now() -> 'FormattedDate':
        return FormattedDate(datetime.now())

    @staticmethod
    def from_week(week_in_year: int) -> 'FormattedDate':
        year = datetime.now().year
        return FormattedDate(datetime.fromisocalendar(year, week_in_year, 7))

    @staticmethod
    def from_format(date: str, format: str) -> 'FormattedDate':
        return FormattedDate(datetime.strptime(date, format))

    def to_format(self, format: str) -> str:
        return self.date.strftime(format)


def get_environmen_var(env_var: str) -> Any:
    result = os.environ.get(env_var)
    if result is None:
        raise ValueError(f'The \'{env_var}\' environment variable is not set.')
    return result


def check_required_environment_variables() -> Any:
    for env_var in ['JSON_FOLDER']:
        get_environmen_var(env_var)
