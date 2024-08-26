from datetime import datetime, timedelta
from functools import reduce
from typing import Any, Dict
from dash import dash_table, dcc, html
from dash.dash import Dash
from fetch_data import DownloadsFetcher, PackageDownloads
import plotly.graph_objs as go
import pandas as pd
from utils import Repository

idx = '2'

if idx == '1':
    fetcher = DownloadsFetcher.from_package_sites()
    fetcher.write_report()
    fetcher.write_json()
else:
    fetcher = DownloadsFetcher.from_json_file("./Output/json2024-08-25.txt")


app = Dash(__name__)


def create_table(fetcher: DownloadsFetcher, section: Repository):
    table_header = [html.Tr([html.Th("Package"), html.Th("Downloads last month"), html.Th("Downloads last week"),
                             html.Th("Avg downloads per day"), html.Th("Libraries.io Score")])]

    table_rows = []
    packages: list[PackageDownloads] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    for package in packages:
        # libraries_io_score = reduce(lambda acc, value: acc + value, package.libraries_io_score.values(), 0)
        package_statistics = package.calculate_monthly_statistics_from_daily_downloads(fetcher.end_date)
        row = html.Tr([
            html.Td(package.package_name),
            html.Td(package_statistics['last_month_downloads']),
            html.Td(package_statistics['last_week_downloads']),
            html.Td(int(package_statistics['avg_daily_downloads'])),
            html.Td(package_statistics['libraries_io_score'])
        ])
        table_rows.append(row)

    return html.Table(table_header + table_rows)


def create_graph(fetcher: DownloadsFetcher, section: Repository) -> Dict[str, Any]:
    packages: list[PackageDownloads] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    downloads_dict = {p.package_name: {d.date: d.downloads for d in p.downloads} for p in packages}
    date_format = '%Y-%m-%d'
    start_date = datetime.strptime(fetcher.start_date, date_format)
    end_date = datetime.strptime(fetcher.end_date, date_format)
    date_range = [(start_date + timedelta(days=x)).strftime(date_format) for x in range((end_date - start_date).days + 1)]

    traces = [
        go.Scatter(
            x=date_range,
            y=[int(downloads_dict[package.package_name].get(d, 0)) for d in date_range],
            mode='lines+markers',
            name=package.package_name
        )
        for package in packages
    ]

    return {
        'data': traces,
        'layout': go.Layout(
            title='Daily Downloads Evolution',
            xaxis={'title': 'Date'},
            yaxis={'title': 'Downloads'},
            hovermode='closest'
        )
    }


app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label=repo.repo_name, children=[
            html.H1(f"{repo.name} Package Downloads"),
            html.H2("Download Data Table"),
            create_table(fetcher, repo),

            html.H2("Download Trends"),
            dcc.Graph(
                id='downloads-graph',
                figure=create_graph(fetcher, repo)
            )
        ])
        for repo in Repository
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
