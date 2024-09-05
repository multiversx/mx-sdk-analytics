import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import dash
import plotly.graph_objs as go
from dash import Input, Output, dcc, html
from dotenv.main import load_dotenv

from fetch_data import DownloadsFetcher, PackageDownloads
from utils import PackagesRegistry

load_dotenv()

app = dash.Dash(__name__)
background_color = '#e6f7ff'
directory = os.environ.get('JSON_FOLDER')

json_files = sorted(Path(directory).glob('blue*.json'), reverse=True)
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
                'BLUE REPORT',
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


def create_table(fetcher: DownloadsFetcher, section: PackagesRegistry):
    header_row = [
        html.Th('Package'),
        html.Th(['Downloads', html.Br(), 'last month']),
        html.Th(['Downloads', html.Br(), 'last week']),
        html.Th(['Avg downloads', html.Br(), 'per day']),
        html.Th(['Libraries.io', html.Br(), 'Score']),
        html.Th(['Site', html.Br(), ' Score']),
        html.Th('Site Score Details')
    ]

    table_header = [html.Tr(header_row)]
    table_rows = []
    packages: list[PackageDownloads] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
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
            html.Td(' - ' + package_statistics['site_score_details'], style={'textAlign': 'right', })
        ]
        table_rows.append(html.Tr(row))

    return html.Table(table_header + table_rows)


def create_package_info_box(fetcher: DownloadsFetcher, section: PackagesRegistry):
    info_boxes = []
    packages: list[PackageDownloads] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)

    for package in packages:
        info = package.analyse_libraries_io_score()
        if info:
            info_boxes.append(html.Div([
                html.H3(package.package_name),
                html.P(info),
            ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin': '10px'}))

    return html.Div(info_boxes)


def create_graph(fetcher: DownloadsFetcher, section: PackagesRegistry) -> Dict[str, Any]:
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


@app.callback(
    Output('report-content', 'children'),
    Input('file-selector', 'value')
)
def update_report(selected_file: str):
    fetcher = DownloadsFetcher.from_generated_file(selected_file)
    return html.Div([
        dcc.Tabs([
            dcc.Tab(label=repo.repo_name, children=[
                html.H1(f"{repo.name} Package Downloads"),
                html.H2('Download Data Table'),
                create_table(fetcher, repo),

                html.H2('Download Trends'),
                dcc.Graph(
                    id='downloads-graph',
                    figure=create_graph(fetcher, repo)
                ),
                html.H2('Libraries.io warnings'),
                create_package_info_box(fetcher, repo)
            ])
            for repo in PackagesRegistry
        ])
    ])


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
