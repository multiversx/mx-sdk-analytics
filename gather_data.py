import argparse

from dotenv.main import load_dotenv

from github_fetcher import GithubFetcher
from package_managers_fetcher import PackageManagersFetcher
from utils import FormattedDate


def validate_date(date_str: str):
    try:
        result_date = FormattedDate.from_string(date_str)
        if result_date > FormattedDate.now():
            raise ValueError()
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{date_str}'. Expected date before {FormattedDate.now()}, format: YYYY-mm-dd.")


def validate_week(week_str: str):
    week_no = int(week_str)
    try:
        result_date = FormattedDate.from_week(week_no)
        if result_date > FormattedDate.now():
            raise ValueError()
        return week_no
    except ValueError:
        max_week_no = FormattedDate.now().isocalendar().week - 1
        raise argparse.ArgumentTypeError(f"Not a valid week number: '{week_no}'. Expected number between 0 and {max_week_no}")


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
        type=validate_week,
        help='Runs the script with end_date as sunday of the week provided.'
    )
    args = parser.parse_args()

    end_date = FormattedDate.now() - 1
    if args.date:
        end_date = FormattedDate.from_string(args.date)
    if args.week:
        end_date = FormattedDate.from_week(args.week)

    print(f"Gathering data for: {end_date}...")
    print(end_date.get_week_and_day_string())

    # Creates a fetcher for retrieving package sites info
    load_dotenv()
    pm_fetcher = PackageManagersFetcher.from_package_sites(str(end_date))
    pm_fetcher.write_json()

    git_fetcher = GithubFetcher.from_package_sites(str(end_date))
    git_fetcher.write_json()


if __name__ == "__main__":
    main()
