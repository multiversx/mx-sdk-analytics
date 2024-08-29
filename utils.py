from enum import Enum


class Language(Enum):
    JAVASCRIPT = 'Javascript'
    RUST = 'Rust'
    PYTHON = 'Python'


class PackagesRegistry(Enum):
    NPM = ('npmjs', [Language.JAVASCRIPT])
    CARGO = ('crates.io', [Language.RUST])
    PYPI = ('pypi', [Language.PYTHON])

    def __init__(self, repo_name: str, languages: list[Language]):
        self.repo_name = repo_name
        self.languages = languages
