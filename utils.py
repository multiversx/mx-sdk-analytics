from enum import Enum
from typing import List


class Language(Enum):
    JAVASCRIPT = 'Javascript'
    TYPESCRIPT = 'Typescript'
    NESTJS = 'Nestjs'
    RUST = 'Rust'
    PYTHON = 'Python'


class Repository(Enum):
    NPM = ('npmjs', [Language.JAVASCRIPT, Language.TYPESCRIPT, Language.NESTJS])
    CARGO = ('crates.io', [Language.RUST])
    PYPI = ('pypi', [Language.PYTHON])

    def __init__(self, repo_name: str, languages: list[Language]):
        self.repo_name = repo_name
        self.languages = languages
