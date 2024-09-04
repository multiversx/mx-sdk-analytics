from datetime import datetime, timedelta
import os
import glob
from pathlib import Path
from typing import Any, Dict, List
import dash
from dash import dcc, html, Input, Output
from dotenv.main import load_dotenv
import plotly.graph_objs as go

from utils import PackagesRegistry, Reports
from github_fetcher import GithubFetcherObject, GithubPackageObject

from constants import DATE_FORMAT


load_dotenv()

app = dash.Dash(__name__)
background_color = '#e6ffe6'
directory = os.environ.get("JSON_FOLDER")

json_files = sorted(Path(directory).glob(f"{"green"}*.json"), reverse=True)
dropdown_options = [{'label': file.name, 'value': str(file)} for file in json_files]

# Layout of the Dash app
app.layout = html.Div(style={'backgroundColor': background_color}, children=[
    html.Div(
        style={
            'display': 'flex',
            'alignItems': 'center'
        },
        children=[
            html.H1(
                'GREEN REPORT',
                style={'marginRight': '20px'}
            ),
            dcc.Dropdown(
                id='file-selector',
                options=dropdown_options,
                value=dropdown_options[0]['value'],  # Set default value as the newest file generated
                clearable=False,
                style={'width': '50%'}
            )
        ]
    ),

    # Container for dynamic content
    html.Div(id='report-content')
])


def create_table(fetcher: GithubFetcherObject, section: PackagesRegistry):
    header_row = [
        html.Th("Package"),
        html.Th(["Downloads", html.Br(), "last month"]),
        html.Th(["Downloads", html.Br(), "last week"]),
        html.Th(["Avg downloads", html.Br(), "per day"]),
        html.Th(["Libraries.io", html.Br(), "Score"]),
        html.Th(["Site", html.Br(), " Score"]),
        html.Th("Site Score Details")
    ]

    table_header = [html.Tr(header_row)]
    table_rows = []
    packages: list[GithubPackageObject] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    for package in packages:
        package_statistics = package.create_summary_of_monthly_statistics_from_daily_downloads(fetcher.end_date)
        row = [
            html.Td(package.package_name),
            html.Td(package_statistics['last_month_downloads'], style={'textAlign': 'right', 'maxWidth': '10ch'}),
            html.Td(package_statistics['last_week_downloads'], style={'textAlign': 'right'}),
            html.Td(int(package_statistics['avg_daily_downloads']), style={'textAlign': 'right'}),
            html.Td(package_statistics['libraries_io_score'], id=f"lio_{package.package_name}", style={'textAlign': 'right'}),
            html.Td(package_statistics['site_score'], style={'textAlign': 'right', 'width': '100px'}),
            html.Td(" - " + package_statistics['site_score_details'], style={'textAlign': 'right', })
        ]
        table_rows.append(html.Tr(row))

    return html.Table(table_header + table_rows)


def create_package_info_box(fetcher: GithubFetcherObject, section: PackagesRegistry):
    info_boxes = []
    packages: list[GithubPackageObject] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)

    for package in packages:
        info = package.analyse_libraries_io_score()
        if info:
            info_boxes.append(html.Div([
                html.H3(package.package_name),
                html.P(info),
            ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin': '10px'}))

    return html.Div(info_boxes)


def create_downloads_graph(fetcher: GithubFetcherObject, section: PackagesRegistry) -> Dict[str, Any]:
    packages: List[GithubPackageObject] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    downloads_dict = {p.package_name: {d.date: d.downloads for d in p.downloads} for p in packages}
    start_date = datetime.strptime(fetcher.start_date, DATE_FORMAT)
    end_date = datetime.strptime(fetcher.end_date, DATE_FORMAT)
    date_range = [(start_date + timedelta(days=x)).strftime(DATE_FORMAT) for x in range((end_date - start_date).days + 1)]

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
            title='Daily Clones Evolution',
            xaxis={'title': 'Date'},
            yaxis={'title': 'Clones'},
            hovermode='closest'
        )
    }


def create_visits_graph(fetcher: GithubFetcherObject, section: PackagesRegistry) -> Dict[str, Any]:
    packages: list[GithubPackageObject] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    views_dict = {p.package_name: {d.date: d.downloads for d in p.views} for p in packages}
    start_date = datetime.strptime(fetcher.start_date, DATE_FORMAT)
    end_date = datetime.strptime(fetcher.end_date, DATE_FORMAT)
    date_range = [(start_date + timedelta(days=x)).strftime(DATE_FORMAT) for x in range((end_date - start_date).days + 1)]

    traces = [
        go.Scatter(
            x=date_range,
            y=[int(views_dict[package.package_name].get(d, 0)) for d in date_range],
            mode='lines+markers',
            name=package.package_name
        )
        for package in packages
    ]

    return {
        'data': traces,
        'layout': go.Layout(
            title='Daily Visits Evolution',
            xaxis={'title': 'Date'},
            yaxis={'title': 'Visits'},
            hovermode='closest'
        )
    }


@app.callback(
    Output('report-content', 'children'),
    Input('file-selector', 'value')
)
def update_report(selected_file: str):
    fetcher = GithubFetcherObject.from_json_file(selected_file)
    return html.Div([
        dcc.Tabs([
            dcc.Tab(label=repo.repo_name, children=[
                html.H1(f"{repo.name} Package Downloads"),
                html.H2("Download Data Table"),
                create_table(fetcher, repo),

                html.H2("Clones Trends"),
                dcc.Graph(
                    id='downloads-graph',
                    figure=create_downloads_graph(fetcher, repo)
                ),
                html.H2("Visits Trends"),
                dcc.Graph(
                    id='visits-graph',
                    figure=create_visits_graph(fetcher, repo)
                ),
                html.H2("Libraries.io warnings"),
                create_package_info_box(fetcher, repo)
            ])
            for repo in [item for item in PackagesRegistry if Reports.GREEN in item.reports]
        ])
    ])


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
