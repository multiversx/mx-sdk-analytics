import os
from pathlib import Path
from typing import Any, Dict, List

import dash
import plotly.graph_objs as go
from dash import Input, Output, dcc, html
from dotenv.main import load_dotenv

from github_fetcher import GithubFetcher, GithubPackage
from utils import FormattedDate, PackagesRegistry, Reports

load_dotenv()

app = dash.Dash(__name__)
background_color = '#e6ffe6'
directory = os.environ.get('JSON_FOLDER')

json_files = sorted(Path(directory).glob('green*.json'), reverse=True)
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


def create_table(fetcher: GithubFetcher, section: PackagesRegistry):
    header_row = html.Thead([
        html.Tr([
            html.Th('Package', rowSpan=3),
            html.Th('Clones', colSpan=5),
            html.Th('Visits', colSpan=5),
            html.Th('No of Forks', rowSpan=3),
            html.Th('No of Stars', rowSpan=3),
            html.Th('No of Watchers', rowSpan=3),
            html.Th('Site score', rowSpan=3),
        ]),
        html.Tr([
            # Clones
            html.Th('Total', colSpan=2),
            html.Th('Last Week', colSpan=2),
            html.Th(['Avg Daily', html.Br(), 'Downloads'], rowSpan=2),
            # Visits
            html.Th('Total', colSpan=2),
            html.Th('Last Week', colSpan=2),
            html.Th(['Avg Daily', html.Br(), 'Visits'], rowSpan=2),
        ]),
        html.Tr([
            # Clones Total
            html.Th('Downloads'),
            html.Th('Downloaders'),
            # Clones Last Week
            html.Th('Downloads'),
            html.Th('Downloaders'),
            # Visits Total
            html.Th('Visits'),
            html.Th('Visitors'),
            # Visits Last Week
            html.Th('Visits'),
            html.Th('Visitors'),
        ])
    ])

    table_header = [header_row]
    table_rows = []
    packages: list[GithubPackage] = [item for item in fetcher.packages if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    for package in packages:
        package_statistics = package.create_summary_statistics_from_daily_downloads(fetcher.end_date)
        row = [
            html.Td(package.package_name),
            html.Td(package_statistics['downloads_total'], style={'textAlign': 'right', 'maxWidth': '10ch'}),
            html.Td(package_statistics['downloaders_total'], style={'textAlign': 'right', 'maxWidth': '10ch'}),
            html.Td(package_statistics['downloads_last_week'], style={'textAlign': 'right'}),
            html.Td(package_statistics['downloaders_last_week'], style={'textAlign': 'right', 'maxWidth': '10ch'}),
            html.Td(int(package_statistics['avg_daily_downloads']), style={'textAlign': 'right'}),
            html.Td(package_statistics['visits_total'], style={'textAlign': 'right', 'maxWidth': '10ch'}),
            html.Td(package_statistics['visitors_total'], style={'textAlign': 'right', 'maxWidth': '10ch'}),
            html.Td(package_statistics['visits_last_week'], style={'textAlign': 'right'}),
            html.Td(package_statistics['visitors_last_week'], style={'textAlign': 'right', 'maxWidth': '10ch'}),
            html.Td(int(package_statistics['avg_daily_visits']), style={'textAlign': 'right'}),

            html.Td(int(package.main_page_statistics['forks_count']), style={'textAlign': 'right'}),
            html.Td(int(package.main_page_statistics['stargazers_count']), style={'textAlign': 'right'}),
            html.Td(int(package.main_page_statistics['watchers_count']), style={'textAlign': 'right'}),
            html.Td(package_statistics['site_score'], style={'textAlign': 'right', 'width': '100px'}),
        ]
        table_rows.append(html.Tr(row))

    return html.Table(table_header + table_rows, style={
        'width': '98%',
        'borderCollapse': 'collapse',
    })


def create_package_info_box(fetcher: GithubFetcher, section: PackagesRegistry):
    info_boxes = []
    packages: list[GithubPackage] = [item for item in fetcher.packages if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)

    for package in packages:
        info = package.analyse_package()
        if info:
            info_boxes.append(html.Div([
                html.H3(package.package_name),
                html.P(info),
            ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin': '10px'}))

    return html.Div(info_boxes)


def create_downloads_graph(fetcher: GithubFetcher, section: PackagesRegistry) -> Dict[str, Any]:
    packages: List[GithubPackage] = [item for item in fetcher.packages if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    downloads_dict = {p.package_name: {d.date: d.downloads for d in p.downloads} for p in packages}
    start_date = FormattedDate.from_string(fetcher.start_date)
    end_date = FormattedDate.from_string(fetcher.end_date)
    date_range = [str(start_date + x) for x in range(end_date.days_from(start_date) + 1)]

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


def create_visits_graph(fetcher: GithubFetcher, section: PackagesRegistry) -> Dict[str, Any]:
    packages: list[GithubPackage] = [item for item in fetcher.packages if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    views_dict = {p.package_name: {d.date: d.downloads for d in p.views} for p in packages}
    start_date = FormattedDate.from_string(fetcher.start_date)
    end_date = FormattedDate.from_string(fetcher.end_date)
    date_range = [str(start_date + x) for x in range(end_date.days_from(start_date) + 1)]

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
    fetcher = GithubFetcher.from_generated_file(selected_file)
    return html.Div([
        dcc.Tabs([
            dcc.Tab(label=repo.repo_name, id=repo.repo_name, children=[
                html.H1(f"{repo.name} Repositories Downloads"),
                html.H2('Two Weeks Download Data Table'),
                create_table(fetcher, repo),
                html.H2('Clones & Visits Trends'),
                html.Div([
                    dcc.Graph(
                        id='downloads-graph',
                        figure=create_downloads_graph(fetcher, repo)
                    ),
                ], style={'display': 'inline-block', 'width': '48%'}),
                html.Div([
                    dcc.Graph(
                        id='visits-graph',
                        figure=create_visits_graph(fetcher, repo)
                    ),
                ], style={'display': 'inline-block', 'width': '48%'}),
                html.H2('Health score warnings'),
                create_package_info_box(fetcher, repo)
            ])
            for repo in [item for item in PackagesRegistry if Reports.GREEN in item.reports]
        ])
    ])


if __name__ == '__main__':
    app.run_server(debug=True, port=8051, host='0.0.0.0')
