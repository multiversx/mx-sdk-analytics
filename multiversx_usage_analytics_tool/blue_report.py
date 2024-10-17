from typing import Any, Dict, cast

import dash
import plotly.graph_objs as go
from dash import Input, Output, dcc, html

from multiversx_usage_analytics_tool.ecosystem_configuration import \
    EcosystemConfiguration
from multiversx_usage_analytics_tool.fetcher import Package
from multiversx_usage_analytics_tool.package_managers_fetcher import (
    PackageManagersFetcher, PackageManagersPackage)
from multiversx_usage_analytics_tool.utils import (FormattedDate,
                                                   PackagesRegistry, Reports,
                                                   get_environment_var)

report_type = Reports.BLUE


app = dash.Dash(__name__)


def get_layout():
    directory = get_environment_var('JSON_FOLDER')
    dropdown_options = report_type.get_report_dropdown_options(directory)
    selected_option = dropdown_options[0]['value'] if dropdown_options else None  # Set default value as the newest file generated
    organization_options = [item.value.name for item in EcosystemConfiguration]

    # Layout of the Dash app
    return html.Div(style={'backgroundColor': report_type.repo_color}, children=[
        html.Div(
            style={
                'display': 'flex',
                'alignItems': 'center'
            },
            children=[
                html.H1(
                    report_type.repo_title,
                    style={'marginRight': '20px', 'width': '30%'}
                ),
                dcc.Dropdown(
                    id='file-selector', maxHeight=1000,
                    options=dropdown_options,
                    value=selected_option,
                    clearable=False,
                    style={'width': '35%'}
                ),
                dcc.RadioItems(organization_options, organization_options[0], id='organization-selector', inline=True, style={'width': '30%'}),
            ]
        ),

        # Container for dynamic content
        html.Div(id='report-content')
    ])


app.layout = get_layout


def create_table(fetcher: PackageManagersFetcher, section: PackagesRegistry):
    header_row = html.Thead([
        html.Th('Package'),
        html.Th(['Downloads', html.Br(), 'last month']),
        html.Th(['Downloads', html.Br(), 'last week']),
        html.Th(['Avg downloads', html.Br(), 'per day']),
        html.Th(['Libraries.io', html.Br(), 'Score']),
        html.Th(['Site', html.Br(), ' Score']),
        html.Th('Site Score Details')
    ])
    table_header = [header_row]
    table_rows = []
    packages: list[Package] = [item for item in fetcher.packages if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    for package in packages:
        package_statistics = package.create_summary_statistics_from_daily_downloads(fetcher.end_date, report_type.repo_length)
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

    return html.Table(table_header + table_rows, id='downloads_table', style={
        'width': '98%',
        'borderCollapse': 'collapse',
    })


def create_package_info_box(fetcher: PackageManagersFetcher, section: PackagesRegistry):
    info_boxes = []
    packages: list[PackageManagersPackage] = [cast(PackageManagersPackage, item) for item in fetcher.packages if item.package_site == section.repo_name]
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
    packages: list[Package] = [item for item in fetcher.packages if item.package_site == section.repo_name]
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
    organization = EcosystemConfiguration[selected_organization.upper()].value
    fetcher = PackageManagersFetcher.from_generated_file(selected_file, organization)
    return html.Div([
        dcc.Tabs([
            dcc.Tab(label=repo.repo_name, id=repo.repo_name.replace('.', '-'), style={'font-weight': 'normal'},
                    selected_style={'font-weight': 'bold'}, children=[
                html.H1(f"{organization.name} - {repo.name} Package Downloads"),
                html.H2('Download Data Table'),
                create_table(fetcher, repo),

                html.H2('Download Trends'),
                dcc.Graph(
                    id='downloads-graph',
                    figure=create_graph(fetcher, repo)
                ),
                html.H2('Libraries.io warnings') if organization.report_warnings else None,
                create_package_info_box(fetcher, repo) if organization.report_warnings else None,
            ])
            for repo in PackagesRegistry if report_type in repo.reports
        ],
            colors={
            "border": "white",  # Border color
            "primary": "blue",  # Color of the selected tab
            "background": "lightgray"  # Color of the unselected tabs
        }),
    ])


if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')
