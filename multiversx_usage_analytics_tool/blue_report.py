import os
from pathlib import Path
from typing import Any, Dict

import dash
import plotly.graph_objs as go
from dash import Input, Output, dcc, html
from dotenv.main import load_dotenv
from package_managers_fetcher import (PackageManagersFetcher,
                                      PackageManagersPackage)
from utils import FormattedDate, PackagesRegistry, Reports

from multiversx_usage_analytics_tool.ecosystem import Organizations

load_dotenv()

app = dash.Dash(__name__)
background_color = '#e6f7ff'
directory = os.environ.get('JSON_FOLDER')
if directory is None:
    raise ValueError("The 'JSON_FOLDER' environment variable is not set.")

json_files = sorted(Path(directory).glob('blue*.json'), reverse=True)
dropdown_options = [{'label': file.name, 'value': str(file)} for file in json_files]
organization_options = [item.value.name for item in Organizations]

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
                style={'width': '40%'}
            ),
            dcc.RadioItems(organization_options, organization_options[0], id='organization-selector', inline=True, style={'width': '40%'}),
        ]
    ),

    # Container for dynamic content
    html.Div(id='report-content')
])


def create_table(fetcher: PackageManagersFetcher, section: PackagesRegistry):
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
    packages: list[PackageManagersPackage] = [item for item in fetcher.packages if item.package_site == section.repo_name]  # type: ignore
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    for package in packages:
        package_statistics = package.create_summary_statistics_from_daily_downloads(fetcher.end_date)
        row = [
            html.Td(package.package_name),
            html.Td(package_statistics['downloads_total'], style={'textAlign': 'right', 'maxWidth': '10ch'}),
            html.Td(package_statistics['downloads_last_week'], style={'textAlign': 'right'}),
            html.Td(int(package_statistics['avg_daily_downloads']), style={'textAlign': 'right'}),
            html.Td(package_statistics['libraries_io_score'], id=f"lio_{package.package_name}", style={'textAlign': 'right'}),
            html.Td(package_statistics['site_score'], style={'textAlign': 'right', 'width': '100px'}),
            html.Td(' - ' + package_statistics['site_score_details'], style={'textAlign': 'right', })
        ]
        table_rows.append(html.Tr(row))

    return html.Table(table_header + table_rows, style={
        'width': '98%',
        'borderCollapse': 'collapse',
    })


def create_package_info_box(fetcher: PackageManagersFetcher, section: PackagesRegistry):
    info_boxes = []
    packages: list[PackageManagersPackage] = [item for item in fetcher.packages if item.package_site == section.repo_name]  # type: ignore
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)

    for package in packages:
        info = package.analyse_libraries_io_score()
        if info:
            info_boxes.append(html.Div([
                html.H3(package.package_name),
                html.P(info),
            ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin': '10px'}))

    return html.Div(info_boxes)


def create_graph(fetcher: PackageManagersFetcher, section: PackagesRegistry) -> Dict[str, Any]:
    packages: list[PackageManagersPackage] = [item for item in fetcher.packages if item.package_site == section.repo_name]  # type: ignore
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
            title='Daily Downloads Evolution',
            xaxis={'title': 'Date'},
            yaxis={'title': 'Downloads'},
            hovermode='closest'
        )
    }


@app.callback(
    Output('report-content', 'children'),
    [Input('file-selector', 'value'),
     Input('organization-selector', 'value')]
)
def update_blue_report(selected_file: str, selected_organization: str):
    organization = Organizations[selected_organization.upper()].value
    fetcher = PackageManagersFetcher.from_generated_file(selected_file, organization)
    return html.Div([
        dcc.Tabs([
            dcc.Tab(label=repo.repo_name, id=repo.repo_name, children=[
                html.H1(f"{repo.name} Package Downloads"),
                html.H2('Download Data Table'),
                create_table(fetcher, repo),  # type: ignore

                html.H2('Download Trends'),
                dcc.Graph(
                    id='downloads-graph',
                    figure=create_graph(fetcher, repo)  # type: ignore
                ),
                html.H2('Libraries.io warnings'),
                create_package_info_box(fetcher, repo)  # type: ignore
            ])
            for repo in PackagesRegistry if Reports.BLUE in repo.reports
        ])
    ])


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
