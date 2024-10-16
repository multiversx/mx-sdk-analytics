from typing import Any, Dict, Iterable, Optional

import elasticsearch.helpers
from elastic_transport._response import ObjectApiResponse
from elasticsearch import Elasticsearch

from multiversx_usage_analytics_tool.constants import (
    ELASTICSEARCH_CONNECTIONS_PER_NODE, ELASTICSEARCH_MAX_RETRIES,
    REQUEST_TIMEOUT, SCAN_BATCH_SIZE, SCROLL_CONSISTENCY_TIME)
from multiversx_usage_analytics_tool.utils import FormattedDate

# based on class Indexer in multiversx-etl


class Indexer:
    def __init__(self, url: str, username: str = "", password: str = ""):
        basic_auth = (username, password) if username and password else None

        self.elastic_search_client = Elasticsearch(
            url,
            max_retries=ELASTICSEARCH_MAX_RETRIES,
            retry_on_timeout=True,
            connections_per_node=ELASTICSEARCH_CONNECTIONS_PER_NODE,
            request_timeout=REQUEST_TIMEOUT,
            basic_auth=basic_auth
        )

    def count_records(self,
                      index_name: str,
                      start_date: Optional[FormattedDate],
                      end_date: Optional[FormattedDate]
                      ) -> int:
        query = self._get_query_object(start_date, end_date)
        return self.elastic_search_client.count(index=index_name, query=query["query"])["count"]

    def get_records(
            self,
            index_name: str,
            start_timestamp: Optional[FormattedDate] = None,
            end_timestamp: Optional[FormattedDate] = None
    ) -> Iterable[Dict[str, Any]]:
        query = self._get_query_object(start_timestamp, end_timestamp)

        records = elasticsearch.helpers.scan(
            client=self.elastic_search_client,
            index=index_name,
            query=query,
            scroll=SCROLL_CONSISTENCY_TIME,
            raise_on_error=True,
            preserve_order=False,
            size=SCAN_BATCH_SIZE,
            request_timeout=None,
            scroll_kwargs=None,
            clear_scroll=True
        )

        return records

    def get_aggregate_records(
            self,
            index_name: str,
            aggregate_key: str = 'user_agent',
            start_timestamp: Optional[FormattedDate] = None,
            end_timestamp: Optional[FormattedDate] = None,
    ) -> ObjectApiResponse[Any]:
        body = self._get_aggregate_query_object(aggregate_key, start_timestamp, end_timestamp)

        records = self.elastic_search_client.search(
            index=index_name,
            body=body,
        )

        return records

    def _get_query_object(
        self,
        start_timestamp: Optional[FormattedDate],
        end_timestamp: Optional[FormattedDate],
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "exists": {
                                "field": "user_agent"
                            }
                        }
                    ],
                    "must_not": [
                        {
                            "term": {
                                "user_agent": ""
                            }
                        }
                    ]
                }
            }
        }

        if start_timestamp is not None or end_timestamp is not None:
            range_filter: Dict[str, Any] = {
                "range": {
                    "@timestamp": {}
                }
            }

            # Add gte to range flter if start is not None
            if start_timestamp is not None:
                range_filter["range"]["@timestamp"]["gte"] = self._to_index_format(start_timestamp)

            # Add lt to the range filter if end is not None
            if end_timestamp is not None:
                range_filter["range"]["@timestamp"]["lt"] = self._to_index_format(end_timestamp)

            # Add data range filter to the query
            query["query"]["bool"]["must"].append(range_filter)

        return query

    def _get_aggregate_query_object(
        self,
        key: str,
        start_timestamp: Optional[FormattedDate],
        end_timestamp: Optional[FormattedDate]
    ) -> Dict[str, Any]:
        query = self._get_query_object(start_timestamp, end_timestamp)

        aggregate = {
            "user_agents": {
                "terms": {
                    "field": key,
                    "size": SCAN_BATCH_SIZE,
                },
                "aggs": {
                    "docs_per_day": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "calendar_interval": "day",
                            "format": "yyyy-MM-dd"
                        }
                    }
                }
            }
        }

        query['aggs'] = aggregate
        body = {
            **query,
            "size": 0,
            "timeout": SCROLL_CONSISTENCY_TIME,
        }

        return body

    @staticmethod
    def _to_index_format(date: FormattedDate) -> str:
        return f'{str(date)}T00:00:00.000Z'
