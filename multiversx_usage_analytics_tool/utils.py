from datetime import datetime, timedelta
from enum import Enum

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
    NPM = ('npmjs', '', '', [Reports.BLUE])
    CARGO = ('crates.io', '', '', [Reports.BLUE])
    PYPI = ('pypi', '', '', [Reports.BLUE])
    GITHUB = ('github', 'https://api.github.com/search/repositories', 'https://api.github.com/repos', [Reports.GREEN])

    def __init__(self, repo_name: str, search_url: str, downloads_url: str, reports: list[Reports]):
        self.repo_name = repo_name
        self.search_url = search_url
        self.downloads_url = downloads_url
        self.reports = reports


class FormattedDate(datetime):
    @classmethod
    def from_string(cls, date_string: str) -> 'FormattedDate':
        try:
            parsed_date = datetime.strptime(date_string, DATE_FORMAT)
            return cls(parsed_date.year, parsed_date.month, parsed_date.day)
        except ValueError:
            raise ValueError(f"Date must be in {DATE_FORMAT} format: {date_string}")

    def __str__(self):
        return self.strftime(DATE_FORMAT)

    def __add__(self, added_days: int) -> 'FormattedDate':  # type: ignore
        result_date = datetime(self.year, self.month, self.day) + timedelta(added_days)
        return FormattedDate(result_date.year, result_date.month, result_date.day)

    def __sub__(self, substracted_days: int) -> 'FormattedDate':  # type: ignore
        result_date = datetime(self.year, self.month, self.day) - timedelta(substracted_days)
        return FormattedDate(result_date.year, result_date.month, result_date.day)

    def __lt__(self, a_date: 'FormattedDate') -> bool:  # type: ignore
        return super().__lt__(a_date)

    def __gt__(self, a_date: 'FormattedDate') -> bool:  # type: ignore
        return super().__gt__(a_date)

    def get_week_and_day_string(self) -> str:
        return f"week= {self.isocalendar().week}, weekday= {self.isocalendar().weekday}"

    def days_from(self, other: 'FormattedDate') -> int:
        return (datetime(self.year, self.month, self.day) - datetime(other.year, other.month, other.day)).days

    @staticmethod
    def from_week(week_in_year: int) -> 'FormattedDate':
        year = FormattedDate.now().year
        return FormattedDate.fromisocalendar(year, week_in_year, 7)

    @staticmethod
    def from_format(date: str, format: str) -> 'FormattedDate':
        return FormattedDate.strptime(date, format)

    def to_format(self, format: str) -> str:
        return self.strftime(format)