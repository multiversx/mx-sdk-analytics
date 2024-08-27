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


def print_repos():
    for repo in Repository:
        print(f"Repository: {repo.name} - {repo.repo_name}")
        # print("Supported languages: ", ', '.join(map(lambda lang: lang.value, repo.languages)))
        print(f"Supported languages:{', '.join(map(lambda lang: lang.value, repo.languages))}")
        print()


# print_repos()
