from datetime import datetime, timedelta
from functools import reduce
import json
import subprocess
from typing import Any, Dict
from bs4 import BeautifulSoup

import requests

class DailyDownloads:
    def __init__(self) -> None:
        self.date = "1980-01-01"
        self.downloads = 0
    def __str__(self) -> str:
        return f"{self.date} - {self.downloads} downloads"
    def __eq__(self, value: object) -> bool:
        if isinstance(value, DailyDownloads):
            return value.date == self.date and value.downloads==self.downloads
        if isinstance(value, str):
            return(value == self.date)
        return False
    def to_dict(self) -> Dict[str, int]:
        return {
            "date": self.date,
            "downloads": self.downloads
        }
    def add_or_update_downloads_in_list(self, my_list: list['DailyDownloads']):
        if self.date in my_list:
            existing_item = next(item for item in my_list if item == self.date)
            existing_item.downloads += self.downloads
        else:
            my_list.append(self)
    @staticmethod
    def from_npm_fetched_data(response:Dict[str, Any]) -> 'DailyDownloads':
        result = DailyDownloads()
        result.date = response.get('day', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result
    @staticmethod
    def from_pypi_fetched_data(response:Dict[str, Any]) -> 'DailyDownloads':
        return DailyDownloads.from_json_file(response)
    @staticmethod
    def from_crates_fetched_data(response:Dict[str, Any]) -> 'DailyDownloads':
        return DailyDownloads.from_json_file(response)       
    @staticmethod
    def from_json_file(response:Dict[str, Any]):
        result = DailyDownloads()
        result.date = response.get('date', '1980-01-01')
        result.downloads = response.get('downloads', 0)
        return result
class PackageDownloads:
    def __init__(self) -> None:
        self.package_name = ''
        self.package_language = ''
        self.package_site = ''
        self.downloads: list[DailyDownloads] = []
        self.no_of_downloads = 0
    def __str__(self):
        print_str = f"PACKAGE = {self.package_name} - language = {self.package_language} - site = {self.package_site} - downloads = {self.no_of_downloads}\n"
        print_str += "\n".join(str(item) for item in self.downloads) 
        print_str += "\n"
        return print_str
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "section_name": self.package_site,
                "package_name": self.package_name,
                "language": self.package_language,
                "no_of_downloads": self.no_of_downloads
            },
            "downloads": [item.to_dict() for item in self.downloads]
        }
    @staticmethod
    def from_npm_fetched_data(package: str, lang: str, response:Dict[str, Any]) -> 'PackageDownloads':
        result = PackageDownloads()
        raw_downloads = response.get('downloads', [])
        result.downloads = [DailyDownloads.from_npm_fetched_data(item) for item in raw_downloads]
        result.package_name = response.get('package', package)
        result.package_language = "Nestjs" if "nestjs" in result.package_name else lang
        result.package_site = 'npmjs'
        result.no_of_downloads = reduce(lambda acc,dd: acc+dd.downloads, result.downloads, 0)
        return result
    @staticmethod
    def from_crates_fetched_data(package: str, lang: str, response:Dict[str, Any]) -> 'PackageDownloads':
        def add_or_update_downloads(my_list: list[DailyDownloads], elem:DailyDownloads):
            if elem.date in my_list:
                existing_item = next(item for item in my_list if item == elem.date)
                existing_item.downloads += elem.downloads
            else:
                my_list.append(elem)
        result = PackageDownloads()
        raw_downloads = response.get('version_downloads', [])
        for elem in raw_downloads:
            new_download_data = DailyDownloads.from_crates_fetched_data(elem)
            add_or_update_downloads(result.downloads, new_download_data)
        raw_downloads = response.get("meta", {}).get("extra_downloads", [])
        for elem in raw_downloads:
            new_download_data = DailyDownloads.from_crates_fetched_data(elem)
            add_or_update_downloads(result.downloads, new_download_data)
        result.package_language = lang
        result.package_name = package
        result.package_site = 'crates.io'
        result.no_of_downloads = reduce(lambda acc,dd: acc+dd.downloads, result.downloads, 0)
        return result
    @staticmethod
    def from_pypi_fetched_data(package: str, lang: str, response:Dict[str, Any]) -> 'PackageDownloads':
        result = PackageDownloads()
        raw_downloads = response.get('data', [])
        result.downloads = [DailyDownloads.from_pypi_fetched_data(item) for item in filter(lambda x: x.get('category','') == "with_mirrors" ,raw_downloads)]
        result.package_language = lang
        result.package_name = response.get('package', package)
        result.package_site = 'pypi'
        result.no_of_downloads = reduce(lambda acc,dd: acc+dd.downloads, result.downloads, 0)
        return result
    @staticmethod
    def from_json_file(response:Dict[str, Any]) -> 'PackageDownloads':
        result = PackageDownloads()
        raw_downloads = response.get('downloads', [])
        result.downloads = [DailyDownloads.from_json_file(item) for item in raw_downloads]
        meta:Dict[str,Any] = response.get('metadata', '')
        result.package_name = meta.get('package_name', '')
        result.package_site = meta.get('section_name', '')
        result.package_language = meta.get('language', '') 
        result.no_of_downloads = meta.get('no_of_downloads', '')
        return result

class DownloadsFetcher:
    def __init__(self) -> None:
        self.start_date = ''
        self.end_date = ''
        self.downloads: list[PackageDownloads] = []
    def __str__(self):
        print_str = f"DOWNLOADS REPORT ({self.start_date} - {self.end_date})\n\n"
        print_str += "\n".join(str(item) for item in self.downloads) 
        print_str += "\n"
        return print_str
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "report_type": "blue",
                "start_date": self.start_date,
                "end_date": self.end_date,
            },
            "records": [item.to_dict() for item in self.downloads]
        }
    def write_report(self):
        print("writting report ...")
        report_name=f"./Output/log{cn_date()}.txt"
        with open(report_name, 'w') as file:
            file.write(str(self))
    def write_json(self):
        print("writting json ...")
        report_name=f"./Output/json{cn_date()}.txt"
        with open(report_name, 'w') as file:
            file.write(json.dumps(self.to_dict(), indent=4))
    #npm api (registry.npmjs.org) - query search result
    def get_npm_package_names(self, pattern: str):
        size=20
        page=0
        packages = []
        while True:
            url = f"https://registry.npmjs.org/-/v1/search?text={pattern}&size={size}&from={page*size}"
            response = requests.get(url).json()
            package_info = response.get('objects', [])
            new_packages = [item.get('package',{}).get('name') for item in package_info if pattern in item.get('package',{}).get('name')]
            packages.extend(new_packages)
            if len(response['objects'])<size:
                break
            page += 1
        return packages
    def fetch_npm_downloads(self,package_name:str):
        url=f"https://api.npmjs.org/downloads/range/{self.start_date}:{self.end_date}/{package_name}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    #crates api (crates/api) - query search result
    def get_crates_package_names(self, pattern: str):
        size=20
        page=0
        packages = []
        while True:
            url = f"https://crates.io/api/v1/crates?q={pattern}&size={size}&from={page*size}"
            response = requests.get(url).json()
            package_info = response.get('crates', [])
            new_packages = [item.get('name') for item in package_info if pattern in item.get('name')]
            packages.extend(new_packages)
            if len(response['crates'])<size:
                break
            page += 1
        return packages
    #<title>package health: 69/100</title>
    def fetch_crates_downloads(self,package_name:str):
        url=f"https://crates.io/api/v1/crates/{package_name}/downloads"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        filtered_data = data.copy()
        date_format = "%Y-%m-%d"
        start = datetime.strptime(self.start_date, date_format).date()
        end = datetime.strptime(self.end_date, date_format).date()
        filtered_data['version_downloads'] = [entry for entry in data['version_downloads'] if self.start_date <= entry['date'] <= self.end_date]
        filtered_data['meta']['extra_downloads'] = [entry for entry in data['meta']['extra_downloads'] if self.start_date <= entry['date'] <= self.end_date]
        return filtered_data
    #pypi http search result scrapping
    def get_pypi_package_names(self, pattern: str):
        size=20
        page=1
        packages = []
        #<span class="package-snippet__name">multiversx-sdk</span>
        while True:
            url = f"https://pypi.org/search/?q={pattern}&page={page}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            package_info = [item for item in soup.find_all("a", class_="package-snippet")]
            new_packages = [item.find("span", class_="package-snippet__name").text.strip() for item in package_info]
            if not new_packages:
                break
            new_packages = [item for item in new_packages if pattern in item]
            packages.extend(new_packages)
            if not new_packages:
                break
            page += 1
        return packages
    def fetch_pypi_downloads(self,package_name:str):
        url=f"https://pypistats.org/api/packages/{package_name}/overall"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        filtered_data = data.copy()
        date_format = "%Y-%m-%d"
        start = datetime.strptime(self.start_date, date_format).date()
        end = datetime.strptime(self.end_date, date_format).date()
        filtered_data['data'] = [entry for entry in data['data'] if self.start_date <= entry['date'] <= self.end_date]
        return filtered_data
        
    @staticmethod
    def from_package_sites():
        result = DownloadsFetcher()
        end_date=datetime.now()-timedelta(1)
        start_date=end_date-timedelta(29)
        result.start_date = start_date.strftime("%Y-%m-%d") #"2024-08-01"
        result.end_date = end_date.strftime("%Y-%m-%d") #"2024-08-07"
        print("fetching from npm ...")
        packages = result.get_npm_package_names("@multiversx/sdk")
        for package_name in packages:
            fetched_downloads=result.fetch_npm_downloads(package_name)
            package_downloads=PackageDownloads.from_npm_fetched_data(package_name,'Javascript',fetched_downloads)
            result.downloads.append(package_downloads)
        print("fetching from crates ...")
        packages = result.get_crates_package_names("multiversx")
        for package_name in packages:
            fetched_downloads=result.fetch_crates_downloads(package_name)
            package_downloads=PackageDownloads.from_crates_fetched_data(package_name,'Rust',fetched_downloads)
            result.downloads.append(package_downloads)
        print("fetching from pypi ...")
        packages = result.get_pypi_package_names("multiversx-sdk")        
        for package_name in packages:
            fetched_downloads=result.fetch_pypi_downloads(package_name)
            package_downloads=PackageDownloads.from_pypi_fetched_data(package_name,'Python',fetched_downloads)
            result.downloads.append(package_downloads)
        return result
    @staticmethod
    def from_json_file(file_name:str):
        with open(file_name, 'r') as file:
            json_data:Dict[str,Any] = json.load(file)
        result = DownloadsFetcher()
        meta:Dict[str,Any] = json_data.get('metadata')
        result.start_date=meta.get('start_date','')
        result.end_date=meta.get('end_date', '')
        result.downloads = [PackageDownloads.from_json_file(item) for item in json_data.get('records',[])]
        with open('report.txt', 'w') as file:
            #file.write(str(result))
            file.write(json.dumps(result.to_dict(), indent=4))
        return result
    
def cn_date():
    current_date = datetime.now()
    return current_date.strftime("%Y-%m-%d")

def search_npm_packages(pattern):
    # Call npm search --json
    command = ['npm', 'search', pattern, '--json']
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    
    packages = json.loads(result.stdout)
    package_names = [pkg['name'] for pkg in packages if pattern.lower() in pkg['name'].lower()]
    
    return package_names


