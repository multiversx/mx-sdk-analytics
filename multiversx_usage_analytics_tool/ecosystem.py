from enum import Enum
from typing import Dict, List

from multiversx_usage_analytics_tool.constants import CRATES_PAGE_SIZE, GITHUB_PAGE_SIZE, NPM_PAGE_SIZE
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
        pattern = self.search_includes[site]
        if site == PackagesRegistry.GITHUB:
            exclude = self.search_excludes[site]
            owner = self.github_name
            size = GITHUB_PAGE_SIZE
            affiliated_string = "+".join(f'user:{item}' for item in self.affiliated_orgs) + '+fork:true+' if self.affiliated_orgs else ''
            return f'{site.search_url}?q={pattern}+in:name+user:{owner}+{affiliated_string}NOT+{exclude}+in:name&per_page={size}&page={page}&sort=stars&order=desc'
        elif site == PackagesRegistry.NPM:
            size = NPM_PAGE_SIZE
            return f'{site.search_url}?text={pattern}&size={size}&from={page * size}'
        elif site == PackagesRegistry.CARGO:
            size = CRATES_PAGE_SIZE
            return f'{site.search_url}?q={pattern}&size={size}&from={page * size}'
        elif site == PackagesRegistry.PYPI:
            return f'{site.search_url}/?q={pattern}&page={page}'
        else:
            return ''

    def get_downloads_url_string(self, site: PackagesRegistry, package_name: str) -> str:
        if site == PackagesRegistry.GITHUB:
            return f'{site.downloads_url}/{package_name}/traffic'
        elif site == PackagesRegistry.NPM:
            return f'{site.downloads_url}'
        elif site == PackagesRegistry.CARGO:
            return f'{site.downloads_url}/{package_name}/downloads'
        elif site == PackagesRegistry.PYPI:
            return f'{site.downloads_url}/{package_name}/overall'
        else:
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
            PackagesRegistry.CARGO: 'solana',
            PackagesRegistry.PYPI: 'solana',
            PackagesRegistry.GITHUB: 'solana',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='solana-labs',
        affiliated_orgs=['anza-xyz', 'michaelhly']
    )
    NEAR = Organization(
        name='Near',
        search_includes={
            PackagesRegistry.NPM: 'near-',
            PackagesRegistry.CARGO: 'near',
            PackagesRegistry.PYPI: 'near',
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
            PackagesRegistry.CARGO: 'avalanche',
            PackagesRegistry.PYPI: 'avalanche',
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
