from enum import Enum
from typing import Dict, List

from multiversx_usage_analytics_tool.constants import GITHUB_PAGE_SIZE
from multiversx_usage_analytics_tool.utils import PackagesRegistry


class Organization:
    def __init__(self, name: str = '', search_includes: Dict[PackagesRegistry, str] = {},
                 search_excludes: Dict[PackagesRegistry, str] = {},
                 github_organization: str = '', affiliated_orgs: List[str] = []) -> None:

        self.name = name
        self.search_includes: Dict[PackagesRegistry, str] = search_includes
        self.search_excludes: Dict[PackagesRegistry, str] = search_excludes
        self.github_name = github_organization
        self.affiliated_orgs = affiliated_orgs

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
            affiliated_string = "+".join(f'user:{item}' for item in self.affiliated_orgs) + '+fork:true+' if self.affiliated_orgs else ''
            return f'{site.search_url}?q={pattern}+in:name+user:{owner}+{affiliated_string}NOT+{exclude}+in:name&per_page={size}&page={page}&sort=stars&order=desc'
        return ''

    def get_downloads_url_string(self, site: PackagesRegistry, package_name: str) -> str:
        if site == PackagesRegistry.GITHUB:
            return f'{site.downloads_url}/{package_name}/traffic'
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
        github_organization='solana-labs',
        affiliated_orgs=['anza-xyz']
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


'''
bearer_token = os.environ.get("MX_GITHUB_TOKEN")
org = Organizations.MULTIVERSX.value
url = org.get_search_url_string(PackagesRegistry.GITHUB, 1)
print(url)
response: Dict[str, Any] = requests.get(url, headers={"Authorization": f"Bearer {bearer_token}"}).json()
package_info: List[Any] = response.get('items', [])
for item in package_info:
    if 'deprecated' in item.get('name'):
        print(item.get('name'))
print(len(package_info))
'''
