from datetime import datetime, timedelta
import os
from dotenv.main import load_dotenv
import argparse

from constants import DATE_FORMAT
from packages_registry_fetcher import PackageRegistryFetcherObject

from github_fetcher import GithubFetcherObject


def validate_date(date_str: str):
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{date_str}'. Expected format: YYYY-mm-dd.")


def main():
    parser = argparse.ArgumentParser(
        description="Fetches data from repository sites for 1 month until end_date.\n Example script: python gather_repository_data --date='2024-05-02'.",
        epilog='If no arguments are provided, the day before current date is used by default for end_date.\n\n'
    )

    parser.add_argument(
        '--date',
        type=validate_date,
        help='Runs the script with provided end_date in the format [yyyy-mm-dd].'
    )
    parser.add_argument(
        '--week',
        type=int,
        help='Runs the script with end_date as sunday of the week provided.'
    )
    args = parser.parse_args()

    end_date = (datetime.now() - timedelta(1)).strftime(DATE_FORMAT)
    if args.date:
        end_date = args.date
    if args.week:
        year = datetime.now().year
        end_date = datetime.fromisocalendar(year, args.week, 7).strftime(DATE_FORMAT)

    print(f"Gathering data for: {end_date}...")
    print(f"week= {datetime.strptime(end_date, DATE_FORMAT).isocalendar().week}, weekday= {datetime.strptime(end_date, DATE_FORMAT).isocalendar().weekday}")

    # Creates a fetcher for retrieving package sites info
    load_dotenv()
    # pm_fetcher = PackageRegistryFetcherObject.from_package_sites(end_date)
    # pm_fetcher.write_json()
    # GithubFetcherObject.get_github_rate_limit(token=os.environ.get("GITHUB_TOKEN"))

    git_fetcher = GithubFetcherObject.from_package_sites(end_date)
    git_fetcher.write_json()


if __name__ == "__main__":
    main()
