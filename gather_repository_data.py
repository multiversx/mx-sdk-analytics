from fetch_data import DownloadsFetcher

# Creates a fetcher for retrieving package sites info
fetcher = DownloadsFetcher.from_package_sites()
fetcher.write_report()
fetcher.write_json()
