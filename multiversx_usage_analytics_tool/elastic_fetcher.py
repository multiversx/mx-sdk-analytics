from typing import Any, Dict, List

from elastic_transport._response import ObjectApiResponse

from multiversx_usage_analytics_tool.constants import DEFAULT_DATE
from multiversx_usage_analytics_tool.ecosystem import Organization
from multiversx_usage_analytics_tool.fetcher import (DailyActivity, Fetcher,
                                                     Package)
from multiversx_usage_analytics_tool.indexer import Indexer
from multiversx_usage_analytics_tool.utils import (FormattedDate, Index,
                                                   Indexes, Reports,
                                                   UserAgentGroups,
                                                   get_environment_var)


class ElasticSearchDailyActivity(DailyActivity):

    @staticmethod
    def from_elastic_search_fetched_data(response: Dict[str, Any]) -> 'ElasticSearchDailyActivity':
        result = ElasticSearchDailyActivity()
        result.date = response.get('key_as_string', DEFAULT_DATE)
        result.downloads = response.get('doc_count', 0)
        return result


class ElasticSearchPackage(Package):

    def get_daily_activity(self, item: Dict[str, Any]):
        return ElasticSearchDailyActivity.from_generated_file(item)

    @staticmethod
    def from_aggregate_elastic_search(response: Dict[str, Any]) -> 'ElasticSearchPackage':
        result = ElasticSearchPackage()
        raw_downloads = response.get('docs_per_day', {}).get('buckets', [])

        result.downloads = [ElasticSearchDailyActivity.from_elastic_search_fetched_data(item) for item in raw_downloads]
        package_name = response.get('key', '')
        result.package_name = package_name
        result.no_of_downloads = response.get('doc_count', 0)
        result.package_site = UserAgentGroups.find(package_name)

        return result


class ElasticSearchFetcher(Fetcher):
    def get_package(self, item: Dict[str, Any]) -> ElasticSearchPackage:
        return ElasticSearchPackage.from_generated_file(item)

    def get_user_agent_aggregate_packages(self, response: dict[str, Any]) -> List[ElasticSearchPackage]:
        raw_downloads = [response[key] for key in response.keys()]
        return [ElasticSearchPackage.from_aggregate_elastic_search(item) for item in raw_downloads]

    def fetch_aggregate_data(self, end_date: str) -> dict[str, Any]:
        indexer = Indexer(
            get_environment_var('ELASTIC_SEARCH_LOGS_URL'),
            get_environment_var('ELASTIC_SEARCH_USER'),
            get_environment_var('ELASTIC_SEARCH_PASSWORD')
        )

        end_timestamp = FormattedDate.from_string(end_date)
        indexes = [Indexes.INGRESS]
        fetch_dict = {}
        for index in indexes:
            fetch_start_date = end_timestamp - index.value.days_to_fetch_in_one_go + 1

            while fetch_start_date > FormattedDate.from_string(self.start_date) - 1:
                resp = self.fetch_data(indexer, index.value, end_timestamp)
                end_timestamp -= index.value.days_to_fetch_in_one_go
                fetch_start_date -= index.value.days_to_fetch_in_one_go

                # merge the results
                for entry in resp.get("aggregations", {}).get("user_agents", {}).get("buckets", []):
                    key = entry.get('key', '')
                    if key not in fetch_dict.keys():
                        fetch_dict[key] = entry
                    else:
                        fetch_dict[key]['doc_count'] += entry['doc_count']
                        fetch_dict[key]['docs_per_day']['buckets'] += entry['docs_per_day']['buckets']
        return fetch_dict

    def fetch_data(self, indexer: Indexer, index: Index, end_timestamp: FormattedDate) -> ObjectApiResponse[Any]:
        index_name = get_environment_var(index.index_name)
        start_timestamp = end_timestamp - index.days_to_fetch_in_one_go + 1
        count = indexer.count_records(index_name, start_timestamp, end_timestamp)
        print(f'fetching from {self.organization.name} {index.index_title} ({start_timestamp} - {end_timestamp}) = {count} documents...')
        resp = indexer.get_aggregate_records(index_name, start_timestamp=start_timestamp, end_timestamp=end_timestamp)

        return resp

    def get_user_agent_grouped_packages(self, raw_packages: List[ElasticSearchPackage]) -> List[ElasticSearchPackage]:
        def add_or_update_downloads(my_list: List[ElasticSearchDailyActivity], elem: ElasticSearchDailyActivity):
            if elem.date in [item.date for item in my_list]:
                existing_item = next(item for item in my_list if item.date == elem.date)
                existing_item.downloads += elem.downloads
            else:
                my_list.append(elem)

        result: List[ElasticSearchPackage] = []

        for package in raw_packages:
            if package.package_site in [item.package_name for item in result]:
                existing_package = next(item for item in result if item.package_name == package.package_site)
                existing_package.no_of_downloads += package.no_of_downloads
                for activity in package.downloads:
                    add_or_update_downloads(existing_package.downloads, activity)  # type: ignore
            else:
                new_package = package
                new_package.package_name = package.package_site
                new_package.package_site = UserAgentGroups.get_group(package.package_name).group_name
                result.append(new_package)

        return result

    @staticmethod
    def from_aggregate_elastic_search(org: Organization, end_date: str) -> 'ElasticSearchFetcher':
        result = ElasticSearchFetcher()
        result.organization = org
        result.end_date = end_date
        result.start_date = str(FormattedDate.from_string(end_date) - Reports.YELLOW.value.repo_length + 1)
        received_data = result.fetch_aggregate_data(end_date)
        raw_packages = result.get_user_agent_aggregate_packages(received_data)  # type: ignore
        result.packages = result.get_user_agent_grouped_packages(raw_packages)  # type: ignore
        return result
