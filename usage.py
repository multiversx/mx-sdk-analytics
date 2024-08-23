import base64
import json
import os
import subprocess
from typing import Any, Dict, List, Set

import requests
from bs4 import BeautifulSoup


def fetch_npm_dependents(package_name: str) -> List[str]:
    dependents: Set[str] = set()
    offset = 0

    while True:
        url = f"https://www.npmjs.com/browse/depended/{package_name}?offset={offset}"
        print("Fetching", url)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        records = [a["href"] for a in soup.find_all('a')]
        records = [d for d in records if d.startswith("/package/")]
        records = [d.replace("/package/", "") for d in records]
        records = [record for record in records if record != package_name]
        records = [record for record in records if not record.startswith("@multiversx/")]

        if not records:
            break

        dependents.update(records)
        offset += 16

    return sorted(list(dependents))


def fetch_npm_metadata(package_name: str) -> Dict[str, Any]:
    # Call npm view --json:
    command = ["npm", "view", "--json", package_name]
    result = subprocess.run(command, capture_output=True, text=True)
    metadata = json.loads(result.stdout)
    return metadata


def search_for_cpp_on_github(package_name: str):
    repositories = search_github(f"{package_name} language:c++")
    return repositories


def search_for_node_package_on_github(package_name: str):
    repositories_a = set(search_github(f"{package_name} filename:package.json"))
    repositories_b = set(search_github(f"{package_name} filename:package-lock.json"))
    repositories_c = set(search_github(f"{package_name} filename:yarn.lock"))

    repositories_set = repositories_a.union(repositories_b).union(repositories_c)
    return list(sorted(repositories_set))


def search_for_python_package_on_github(package_name: str):
    repositories_a = search_github(f"{package_name} filename:setup.py")
    repositories_b = search_github(f"{package_name} filename:requirements.txt")
    repositories = repositories_a + repositories_b
    return repositories


def search_github(query: str) -> List[str]:
    # https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28
    # languages: https://github.com/github-linguist/linguist/blob/master/lib/linguist/languages.yml
    # https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax

    github_auth_token = os.environ.get("GITHUB_TOKEN_PUBLIC_READ_ONLY")
    github_search_url = "https://api.github.com/search/code"
    github_api_headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_auth_token}",
    }

    all_items: List[Dict[str, Any]] = []

    response = requests.get(github_search_url, headers=github_api_headers, params={"q": query})
    data = response.json()

    print(json.dumps(data, indent=4), file=open("data.json", "w"))

    all_items.extend(data["items"])

    query_with_forks = f"{query} forks:true"
    response = requests.get(github_search_url, headers=github_api_headers, params={"q": query_with_forks})
    data = response.json()
    all_items.extend(data["items"])

    repositories: Set[str] = set()

    for item in all_items:
        owner_login = item["repository"]["owner"]["login"]
        # if owner_login == "multiversx":
        #     continue

        full_name = item["repository"]["full_name"]
        repositories.add(full_name)

    return sorted(list(repositories))


def fetch_github_file(repository: str, file_path: str):
    github_auth_token = os.environ.get("GITHUB_TOKEN_PUBLIC_READ_ONLY")
    github_api_headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_auth_token}",
    }

    url = f"https://api.github.com/repos/{repository}/contents/{file_path}"
    response = requests.get(url, headers=github_api_headers)
    data = response.json()

    if "content" in data:
        content = data["content"]
        content = base64.b64decode(content.encode("utf-8"))
        return content.decode("utf-8")

    return ""


def grep_file(content: str, pattern: str):
    lines = content.split("\n")
    lines = [line for line in lines if pattern in line]
    return lines


if __name__ == "__main__":
    repositories = search_for_node_package_on_github("@multiversx/sdk-dapp")
    for repo in repositories:
        print(f"https://github.com/{repo}")

        package_json = fetch_github_file(repo, "package.json")
        if package_json:
            print(grep_file(package_json, "@multiversx/sdk-dapp"))

    # packages = fetch_npm_dependents("@multiversx/sdk-dapp")
    # for package in packages:
    #     print(f"https://npmjs.com/package/{package}")

    # repositories = search_for_python_package_on_github("multiversx")
    # print(len(repositories))

    # for repo in repositories:
    #     print(repo)

    # dependents = fetch_npm_dependents("@multiversx/sdk-core")
    # print(len(dependents))

    # for dependent in dependents:
    #     print(dependent)
    #     metadata = fetch_npm_metadata(dependent)
    #     print(metadata.get("description"))