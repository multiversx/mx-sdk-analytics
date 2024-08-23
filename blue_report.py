from fetch_data import DownloadsFetcher


fetcher = DownloadsFetcher.from_package_sites()
fetcher.write_report()
fetcher.write_json()
# fetcher1 = DownloadsFetcher.from_json_file("./Output/json2024-08-23.txt")
