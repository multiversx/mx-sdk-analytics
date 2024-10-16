import json
from typing import Any, Dict, List

from multiversx_usage_analytics_tool.fetcher import DailyActivity, Fetcher, Package
from multiversx_usage_analytics_tool.constants import DEFAULT_DATE
from multiversx_usage_analytics_tool.ecosystem import Organization
from multiversx_usage_analytics_tool.utils import Indexes, UserAgentGroup


class ElasticDailyActivity(DailyActivity):

    @staticmethod
    def from_elastic_search_fetched_data(response: Dict[str, Any]) -> 'ElasticDailyActivity':
        result = ElasticDailyActivity()
        result.date = response.get('key_as_string', DEFAULT_DATE)
        result.downloads = response.get('doc_count', 0)
        return result


class ElasticPackage(Package):

    def get_daily_activity(self, item: Dict[str, Any]):
        return ElasticDailyActivity.from_generated_file(item)

    @staticmethod
    def from_aggregate_elastic_search(elastic_source: str, response: Dict[str, Any]) -> 'ElasticPackage':
        result = ElasticPackage()
        raw_downloads = response.get('docs_per_day', {}).get('buckets', [])

        result.downloads = [ElasticDailyActivity.from_elastic_search_fetched_data(item) for item in raw_downloads]
        package_name = response.get('key', '')
        result.package_name = package_name
        result.no_of_downloads = response.get('doc_count', 0)
        result.package_site = UserAgentGroup.find(package_name)
        result.package_language = elastic_source
        return result


class ElasticFetcher(Fetcher):
    def get_package(self, item: Dict[str, Any]) -> ElasticPackage:
        return ElasticPackage.from_generated_file(item)

    def get_user_agent_aggregate_packages(self, elastic_source: str, response: Dict[str, Any]) -> List[ElasticPackage]:
        raw_downloads = response.get("aggregations", {}).get("useragent_aggregation", {}).get("buckets", [])
        return [ElasticPackage.from_aggregate_elastic_search(elastic_source, item) for item in raw_downloads]

    def fetch_aggregate_data(self, index: str) -> Dict[str, Any]:
        # TODO
        file_name = './TestingData/elastic_aggregate.json'
        with open(file_name, 'r') as file:
            received_json: Dict[str, Any] = json.load(file)
        return received_json

    def fetch_detailed_data(self, index: str) -> Dict[str, Any]:
        # TODO
        received_json = {}
        return received_json

    @staticmethod
    def from_aggregate_elastic_search(org: Organization, end_date: str) -> 'ElasticFetcher':
        result = ElasticFetcher()
        result.organization = org
        result.end_date = end_date
        for idx in Indexes:
            received_json = result.fetch_aggregate_data(idx.index_value)
            result.packages.extend(result.get_user_agent_aggregate_packages(idx.index_name, received_json))  # type: ignore
        return result
