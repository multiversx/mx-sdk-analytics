import json
from pathlib import Path

from blue_report import EcosystemConfiguration

from multiversx_usage_analytics_tool.elastic_fetcher import ElasticFetcher
from multiversx_usage_analytics_tool.utils import (FormattedDate, Reports,
                                                   get_environment_var)


def main():
    end_date = FormattedDate.now() - 1

    print(f"Gathering data for: {end_date}...")
    print(end_date.get_week_and_day_string())

    # Creates a fetcher for retrieving elastic search data

    rep_folder = get_environment_var("JSON_FOLDER")
    el_dict_to_write = {}
    org = EcosystemConfiguration.MULTIVERSX.value
    el_fetcher = ElasticFetcher.from_aggregate_elastic_search(org, str(end_date))
    el_dict_to_write[org.name] = el_fetcher.to_dict()

    report_type = Reports.YELLOW
    print("writting json ...")
    el_report_name = Path(rep_folder if rep_folder else ".") / f"{report_type.repo_name}{end_date}.json"
    el_report_name.write_text(json.dumps(el_dict_to_write, indent=4))


if __name__ == "__main__":
    main()
