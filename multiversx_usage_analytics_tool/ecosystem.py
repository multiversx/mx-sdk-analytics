from typing import Any, Dict, List

from multiversx_usage_analytics_tool.constants import (CRATES_PAGE_SIZE,
                                                       GITHUB_PAGE_SIZE,
                                                       NPM_PAGE_SIZE)
from multiversx_usage_analytics_tool.utils import (PackagesRegistries,
                                                   PackagesRegistry)


class Organization:
    def __init__(self,
                 name: str = '',
                 gather_data: bool = False,
                 report_warnings: bool = False,
                 search_includes: Dict[str, str] = {},
                 search_excludes: Dict[str, str] = {},
                 github_organization: str = '',
                 affiliated_orgs: List[str] = []
                 ) -> None:

        self.name = name
        self.gather_data = gather_data
        self.report_warnings = report_warnings
        self.search_includes = search_includes
        self.search_excludes = search_excludes
        self.github_name = github_organization
        self.affiliated_orgs = affiliated_orgs

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Organization):
            return (value.name == self.name)
        return False

    def get_search_url_string(self, site: PackagesRegistry, page: int) -> str:
        pattern = self.search_includes[site.repo_name]
        if site == PackagesRegistries.GITHUB.value:
            exclude = self.search_excludes[site.repo_name]
            owner = self.github_name
            size = GITHUB_PAGE_SIZE
            affiliated_string = "+".join(f'user:{item}' for item in self.affiliated_orgs) + '+fork:true+' if self.affiliated_orgs else ''
            return f'{site.search_url}?q={pattern}+in:name+user:{owner}+{affiliated_string}NOT+{exclude}+in:name&per_page={size}&page={page}&sort=stars&order=desc'
        elif site == PackagesRegistries.NPM.value:
            size = NPM_PAGE_SIZE
            return f'{site.search_url}?text={pattern}&size={size}&from={page * size}'
        elif site == PackagesRegistries.CARGO.value:
            size = CRATES_PAGE_SIZE
            return f'{site.search_url}'
        elif site == PackagesRegistries.PYPI.value:
            return f'{site.search_url}/?q={pattern}&page={page}'
        else:
            raise ValueError(f'Unknown package registry\'{site.repo_name}\'.')

    def get_search_filter(self, site: PackagesRegistry, item: Dict[str, Any]) -> bool:
        if not item:
            return False
        pattern = self.search_includes[site.repo_name]
        own_github_orgs = [f'github.com/{item}/' for item in self.affiliated_orgs + [self.github_name]]

        if site == PackagesRegistries.NPM.value:
            item_name = item.get('package', {}).get('name')
            item_repository = item.get('package', {}).get('links', {}).get('repository', '')
            item_scope = item.get('package', {}).get('scope', '')
            return pattern in item_name and (self.name.lower() in item_scope or isinstance(item_repository, str) and any(
                own_repo_str in item_repository for own_repo_str in own_github_orgs))

        elif site == PackagesRegistries.CARGO.value:
            item_name = item.get('name', '')
            item_repository = item.get('repository', '')
            return pattern in item_name and isinstance(item_repository, str) and any(own_repo_str in item_repository for own_repo_str in own_github_orgs)

        elif site == PackagesRegistries.PYPI.value:
            source_url = item.get('Source', '')
            homepage_url = item.get('Homepage', '')
            return any(own_str in source_url for own_str in own_github_orgs) or any(own_str in homepage_url for own_str in own_github_orgs)
        return False

    def get_downloads_url_string(self, site: PackagesRegistry, package_name: str) -> str:
        if site == PackagesRegistries.GITHUB.value:
            return f'{site.downloads_url}/{package_name}/traffic'
        elif site == PackagesRegistries.NPM.value:
            return f'{site.downloads_url}'
        elif site == PackagesRegistries.CARGO.value:
            return f'{site.downloads_url}/{package_name}/downloads'
        elif site == PackagesRegistries.PYPI.value:
            return f'{site.downloads_url}/{package_name}/overall'
        else:
            raise ValueError(f'Unknown package registry\'{site.repo_name}\'.')
