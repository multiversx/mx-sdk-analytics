from enum import Enum
from typing import Dict

from multiversx_usage_analytics_tool.constants import GITHUB_PAGE_SIZE
from multiversx_usage_analytics_tool.utils import PackagesRegistry


class Organization:
    def __init__(self, name: str = '', search_includes: Dict[PackagesRegistry, str] = {},
                 search_excludes: Dict[PackagesRegistry, str] = {}, github_organization: str = '') -> None:
        self.name = name
        self.search_includes: Dict[PackagesRegistry, str] = search_includes
        self.search_excludes: Dict[PackagesRegistry, str] = search_excludes
        self.github_name = github_organization

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Organization):
            return (value.name == self.name)
        return False

    def get_search_url_string(self, site: PackagesRegistry, page: int) -> str:
        if site == PackagesRegistry.GITHUB:
            pattern = self.search_includes[site]
            exclude = self.search_excludes[site]
            owner = self.github_name
            size = GITHUB_PAGE_SIZE
            return f'{site.search_url}?q={pattern}+in:name-{exclude}+in:name+user:{owner}&per_page={size}&page={page}&sort=stars&order=desc'
        return ''

    def get_downloads_url_string(self, site: PackagesRegistry) -> str:
        if site == PackagesRegistry.GITHUB:
            return f'{site.downloads_url}/{self.github_name}'
        return ''


class Organizations(Enum):
    MULTIVERSX = Organization(
        name='Multiversx',
        search_includes={
            PackagesRegistry.NPM: '@multiversx/sdk',
            PackagesRegistry.CARGO: 'multiversx',
            PackagesRegistry.PYPI: 'multiversx-sdk',
            PackagesRegistry.GITHUB: 'sdk',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='multiversx'
    )
    SOLANA = Organization(
        name='Solana',
        search_includes={
            PackagesRegistry.NPM: '@solana',
            PackagesRegistry.CARGO: 'multiversx',
            PackagesRegistry.PYPI: 'multiversx-sdk',
            PackagesRegistry.GITHUB: '',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='solana-labs'
    )
    NEAR = Organization(
        name='Near',
        search_includes={
            PackagesRegistry.NPM: 'near-',
            PackagesRegistry.CARGO: 'multiversx',
            PackagesRegistry.PYPI: 'multiversx-sdk',
            PackagesRegistry.GITHUB: 'near',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='near'
    )
    AVALANCHE = Organization(
        name='Avalanche',
        search_includes={
            PackagesRegistry.NPM: '@avalabs/',
            PackagesRegistry.CARGO: 'multiversx',
            PackagesRegistry.PYPI: 'multiversx-sdk',
            PackagesRegistry.GITHUB: '',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='ava-labs'
    )
