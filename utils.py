from enum import Enum


class Reports (Enum):
    BLUE = 'blue'
    GREEN = 'green'


class Language(Enum):
    JAVASCRIPT = 'Javascript'
    RUST = 'Rust'
    PYTHON = 'Python'


class PackagesRegistry(Enum):
    NPM = ('npmjs', [Language.JAVASCRIPT], [Reports.BLUE])
    CARGO = ('crates.io', [Language.RUST], [Reports.BLUE])
    PYPI = ('pypi', [Language.PYTHON], [Reports.BLUE])
    GITHUB = ('github', [Language.JAVASCRIPT, Language.PYTHON, Language.RUST], [Reports.GREEN])

    def __init__(self, repo_name: str, languages: list[Language], reports: list[Reports]):
        self.repo_name = repo_name
        self.languages = languages
        self.reports = reports
