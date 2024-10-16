import json
import os
from pathlib import Path
from dotenv.main import load_dotenv
from multiversx_usage_analytics_tool.utils import FormattedDate, Reports
from multiversx_usage_analytics_tool.elastic_fetcher import ElasticFetcher

from blue_report import EcosystemConfiguration


def main():
    end_date = FormattedDate.now()

    print(f"Gathering data for: {end_date}...")
    print(end_date.get_week_and_day_string())

    # Creates a fetcher for retrieving package sites info
    load_dotenv()

    rep_folder = os.environ.get("JSON_FOLDER")
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
