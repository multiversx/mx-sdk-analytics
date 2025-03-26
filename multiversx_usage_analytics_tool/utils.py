import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, List, Tuple

import inquirer
from dotenv.main import load_dotenv
from playwright.async_api import Browser, Page, Playwright
from pypdf import PdfWriter

from multiversx_usage_analytics_tool.constants import (
    BLUE_REPORT_PORT, DATE_FORMAT, DAYS_IN_MONTHLY_REPORT,
    DAYS_IN_TWO_WEEKS_REPORT, DAYS_IN_WEEK, GREEN_REPORT_PORT,
    WAIT_FOR_DROPDOWN_COMPONENT_LOAD, YELLOW_REPORT_PORT)


@dataclass
class Report:
    repo_name: str
    repo_title: str
    repo_color: str
    repo_port: int
    repo_length: int

    def get_report_dropdown_options(self, folder: str):
        json_files = sorted(Path(folder).glob(f'{self.repo_name}*.json'), reverse=True)
        return [{'label': file.name, 'value': str(file)} for file in json_files]


class Reports (Enum):
    BLUE = Report('blue', 'PACKAGE MANAGERS REPORT', '#e6f7ff', BLUE_REPORT_PORT, DAYS_IN_MONTHLY_REPORT)
    GREEN = Report('green', 'GITHUB REPORT', '#e6ffe6', GREEN_REPORT_PORT, DAYS_IN_TWO_WEEKS_REPORT)
    YELLOW = Report('yellow', 'USER AGENT REPORT', '#FFFFF0', YELLOW_REPORT_PORT, DAYS_IN_TWO_WEEKS_REPORT)


@dataclass
class Index:
    index_title: str
    index_name: str
    days_to_fetch_in_one_go: int


class Indexes(Enum):
    ACCESS = Index('Access-logs', 'ACCESS_INDEX_NAME', DAYS_IN_TWO_WEEKS_REPORT)
    INGRESS = Index('Ingress-logs', 'INGRESS_INDEX_NAME', DAYS_IN_WEEK)


@dataclass
class Language:
    lang_name: str
    suffixes: list[str]


class Languages(Enum):
    JAVASCRIPT = Language('Javascript', ['js', 'nestjs'])
    RUST = Language('Rust', ['rs', 'rust'])
    PYTHON = Language('Python', ['py'])
    CSHARP = Language('C#', ['csharp'])
    C = Language('C/C++', ['clang', 'cpp'])
    GO = Language('Go', ['go'])
    PHP = Language('PHP', ['php'])
    JAVA = Language('Java', ['java'])
    KOTLIN = Language('Kotlin', ['kotlin'])
    UNKNOWN = Language('Unknown', ['unknown'])


@dataclass()
class PackagesRegistry:
    repo_name: str
    search_url: str
    downloads_url: str
    reports: list[Report]


class PackagesRegistries(Enum):
    NPM = PackagesRegistry('npmjs', 'https://registry.npmjs.org/-/v1/search', 'https://api.npmjs.org/downloads/range', [Reports.BLUE.value])
    CARGO = PackagesRegistry('crates.io', 'https://crates.io/api/v1/crates', 'https://crates.io/api/v1/crates', [Reports.BLUE.value])
    PYPI = PackagesRegistry('pypi', 'https://pypi.org/search', 'https://pypistats.org/api/packages', [Reports.BLUE.value])
    GITHUB = PackagesRegistry('github', 'https://api.github.com/search/repositories', 'https://api.github.com/repos', [Reports.GREEN.value])


@dataclass
class UserAgentGroup:
    group_name: str
    group_prefixes: List[str]


class UserAgentGroups(Enum):
    MULTIVERSX = UserAgentGroup('Multiversx', ['multiversx', 'mx-'])
    PYTHON = UserAgentGroup('Python', ['python'])
    AXIOS = UserAgentGroup('Axios', ['axios'])
    HTTPS = UserAgentGroup('Https', ['^mozilla.*\\+http', '^safari.*\\+http', '^opera.*\\+http'])
    MOBILE_IOS = UserAgentGroup('Mobile IOS', ['^mozilla.*iphone', '^safari.*iphone', '^opera.*iphone'])
    MOBILE_ANDROID = UserAgentGroup('Mobile Android', ['^mozilla.*android', '^safari.*android', '^opera.*android'])
    BROWSER = UserAgentGroup('Desktop browser', ['mozilla', 'opera', 'safari'])
    OKHTTP = UserAgentGroup('Okhttp', ['okhttp'])
    APACHE = UserAgentGroup('Apache-HttpClient', ['apache-httpclient'])
    POSTMAN = UserAgentGroup('PostmanRuntime', ['postmanruntime'])
    CURL = UserAgentGroup('Curl', ['^curl'])

    OTHER = UserAgentGroup('Other', ['@@'])
    UNKNOWN = UserAgentGroup('Unknown', ['group-prefix'])

    @staticmethod
    def find(user_agent_name: str) -> str:
        group = UserAgentGroups.get_group(user_agent_name)
        if group in [UserAgentGroups.MULTIVERSX.value, UserAgentGroups.UNKNOWN.value]:
            return user_agent_name
        elif group in [UserAgentGroups.AXIOS.value, UserAgentGroups.PYTHON.value, UserAgentGroups.APACHE.value,
                       UserAgentGroups.OKHTTP.value, UserAgentGroups.CURL.value]:
            i = user_agent_name.index('/')
            return user_agent_name[:(i + 2)]
        elif group == UserAgentGroups.HTTPS.value:
            url_match = re.search(r'\+(https?://[^\s;)\]]+)', user_agent_name)
            url = url_match.group(1) if url_match else None
            return f'URL: {url}'
        return group.group_name

    @staticmethod
    def get_group(user_agent_name: str) -> UserAgentGroup:
        group = next(
            (group for group in [item.value for item in UserAgentGroups] if any(
                re.search(UserAgentGroups._safe_pattern(pattern), user_agent_name, re.IGNORECASE) for pattern in group.group_prefixes
            )
            ), UserAgentGroups.UNKNOWN.value)

        return group

    @staticmethod
    def _safe_pattern(pattern: str) -> str:
        try:
            re.compile(pattern)
            return pattern
        except re.error:
            return re.escape(pattern)


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


def get_environment_var(env_var: str) -> Any:
    load_dotenv()
    result = os.environ.get(env_var)
    if result is None:
        raise ValueError(f'The \'{env_var}\' environment variable is not set.')
    return result


# save to pdf common methods

def combine_pdfs(pdf_files: List[str], output_pdf: str):
    merger = PdfWriter()

    for pdf in pdf_files:
        merger.append(pdf)

    merger.write(output_pdf)
    merger.close()

    print(f"Combined PDF saved as: {output_pdf}")


async def get_playwright_page(p: Playwright, report_type: Report) -> Tuple[Browser, Page]:
    report_port = report_type.repo_port
    DASH_APP_URL = f'http://0.0.0.0:{report_port}/'

    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(DASH_APP_URL)

    return (browser, page)


async def select_report(page: Page, selected_file: str) -> str:
    wait_for_dropdown_selection_to_load_time = WAIT_FOR_DROPDOWN_COMPONENT_LOAD

    # click on selected file received from dash
    file_selector_id = 'file-selector'
    await page.wait_for_selector(f'#{file_selector_id}', timeout=5000)

    if selected_file:
        desired_value = selected_file.split('/')[-1]  # extract file name without path
        await page.click(f'#{file_selector_id} .Select-control')
        await page.wait_for_selector('.Select-menu-outer')

        files = await page.evaluate('''() => {
            let elements = document.querySelectorAll('.VirtualizedSelectOption');
            let options_text = [];
            elements.forEach(option => options_text.push(option.textContent));
            return options_text;
        }''')
        desired_index = None
        for index, option in enumerate(files):
            if desired_value in option:
                desired_index = index
                break

        if desired_index is not None:
            option_selector = f'.Select-menu-outer .VirtualizedSelectOption:nth-child({desired_index + 1})'
            await page.click(option_selector)
            await page.wait_for_timeout(wait_for_dropdown_selection_to_load_time)

    # Get the selected json file name
    selected_value: str = await page.evaluate(f'''
        document.querySelector("#{file_selector_id}").textContent;
    ''')
    print()
    print(f"Target report: {selected_value}")
    file_name = selected_value.split('.')[0]  # extract name without extension
    output = f'{file_name}.pdf' if any(repo_type in selected_value for repo_type in ['blue', 'green', 'yellow']) else 'combined.pdf'

    return output


async def is_empty_page(page: Page) -> bool:
    await page.wait_for_selector('#downloads_table')
    no_of_rows = await page.evaluate('''
        (function() {
            var table = document.querySelector('#downloads_table');
            if (table) {
                var rows = table.querySelectorAll('tbody tr, tr:not(thead tr)');
                return rows.length;
            } else {
                return 0;
            }
        })();
    ''')
    return no_of_rows == 0


def select_target_json_file(report_type: Report) -> str:
    report_port = report_type.repo_port
    print(f'\nWARNING! Report should be available at port {report_port}.\n')

    # display list of available json files
    directory = get_environment_var('JSON_FOLDER')

    json_files = sorted(Path(directory).glob(f'{report_type.repo_name}*.json'), reverse=True)
    file_options = [file.name for file in json_files]

    questions = [
        inquirer.List('selected_file',
                      message="Select a JSON file",
                      choices=file_options,
                      ),
    ]

    answers = inquirer.prompt(questions)
    return answers['selected_file'] if answers else ''
