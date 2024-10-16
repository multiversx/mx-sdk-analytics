import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, List

import inquirer
from dotenv.main import load_dotenv
from PyPDF2._merger import PdfMerger
from pyppeteer.browser import Browser
from pyppeteer.page import Page

from multiversx_usage_analytics_tool.constants import (
    BLUE_REPORT_PORT, DATE_FORMAT, GREEN_REPORT_PORT,
    WAIT_FOR_DROPDOWN_COMPONENT_LOAD)


class Reports (Enum):
    BLUE = ('blue', 'PACKAGE MANAGERS REPORT', '#e6f7ff')
    GREEN = ('green', 'GITHUB REPORT', '#e6ffe6')
    YELLOW = ('yellow', 'USER AGENT REPORT', '#FFFFF0')

    def __init__(self, repo_name: str, repo_title: str, repo_color: str):
        self.repo_name = repo_name
        self.repo_title = repo_title
        self.repo_color = repo_color


class Indexes(Enum):
    ACCESS = ('Access-logs', 'enriched-mainnet-access-logs')
    INGRESS = ('Ingress-logs', 'enriched-mainnet-ingress-logs')

    def __init__(self, index_name: str, index_value: str):
        self.index_name = index_name
        self.index_value = index_value


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


class UserAgentGroup(Enum):
    MULTIVERSX = ('Multiversx', ['multiversx', 'mx-'])
    PYTHON = ('Python', ['python/3.', 'python-requests/2.'])
    AXIOS = ('Axios', ['axios'])
    MOBILE_ANDROID = ('Mobile Android', ['android'])
    MOBILE_IOS = ('Mobile IOS', ['iphone'])
    BROWSER = ('Browser', ['mozilla', 'opera'])

    OTHER = ('Other/Unknown', ['other/unknown'])

    def __init__(self, group_name: str, group_prefixes: List[str]):
        self.group_name = group_name
        self.group_prefixes = group_prefixes

    @staticmethod
    def find(user_agent_name: str) -> str:
        group_name = next(
            (user_agent.group_name for user_agent in UserAgentGroup if user_agent is not UserAgentGroup.MULTIVERSX and any(
                u in user_agent_name.lower() for u in user_agent.group_prefixes
            )
            ), user_agent_name)
        return group_name


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
    result = os.environ.get(env_var)
    if result is None:
        raise ValueError(f'The \'{env_var}\' environment variable is not set.')
    return result


def check_required_environment_variables() -> Any:
    for env_var in ['JSON_FOLDER']:
        get_environment_var(env_var)


# save to pdf common methods

def combine_pdfs(pdf_files: List[str], output_pdf: str):
    merger = PdfMerger()

    for pdf_file in pdf_files:
        merger.append(pdf_file)

    merger.write(output_pdf)
    merger.close()
    print(f"Combined PDF saved as: {output_pdf}")


async def get_pyppeteer_page(browser: Browser, report_type: Reports) -> Page:
    report_port = GREEN_REPORT_PORT if report_type == Reports.GREEN else BLUE_REPORT_PORT

    page = await browser.newPage()
    await page.setViewport({'width': 1440, 'height': 1080})
    DASH_APP_URL = f'http://0.0.0.0:{report_port}/'
    await page.goto(DASH_APP_URL)

    return page


async def select_report(page: Page, selected_file: str) -> str:
    wait_for_dropdown_selection_to_load_time = WAIT_FOR_DROPDOWN_COMPONENT_LOAD
    # click on selected file received from dash
    file_selector_id = 'file-selector'
    await page.waitForSelector(f'#{file_selector_id}')
    if selected_file:
        desired_value = selected_file.split('/')[-1]  # extract file name without path
        await page.click(f'#{file_selector_id} .Select-control')
        await page.waitForSelector('.Select-menu-outer')

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
            page.waitFor(wait_for_dropdown_selection_to_load_time)

    # Get the selected json file name
    selected_value: str = await page.evaluate(f'''
        document.querySelector("#{file_selector_id}").textContent;
    ''')
    print()
    print(f"Target report: {selected_value}")
    file_name = selected_value.split('.')[0]  # extract name without extension
    output = f'{file_name}.pdf' if any(repo_type in selected_value for repo_type in ['blue', 'green']) else 'combined.pdf'

    return output


async def is_empty_page(page: Page) -> bool:
    await page.waitForSelector('#downloads_table')
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


def select_target_json_file(report_type: Reports) -> str:
    report_port = GREEN_REPORT_PORT if report_type == Reports.GREEN else BLUE_REPORT_PORT
    print(f'\nWARNING! Report should be available at port {report_port}.\n')
    # display list of available json files
    load_dotenv()
    directory = get_environment_var('JSON_FOLDER')

    json_files = sorted(Path(directory).glob(f'{report_type.value}*.json'), reverse=True)
    file_options = [file.name for file in json_files]

    questions = [
        inquirer.List('selected_file',
                      message="Select a JSON file",
                      choices=file_options,
                      ),
    ]

    answers = inquirer.prompt(questions)
    return answers['selected_file'] if answers else ''
