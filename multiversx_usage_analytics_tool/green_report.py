from typing import Any, Dict, List

import dash
import plotly.graph_objs as go
from dash import Input, Output, dcc, html

from multiversx_usage_analytics_tool.ecosystem_configuration import \
    EcosystemConfiguration
from multiversx_usage_analytics_tool.github_fetcher import (GithubFetcher,
                                                            GithubPackage)
from multiversx_usage_analytics_tool.utils import (FormattedDate, Language,
                                                   PackagesRegistries,
                                                   PackagesRegistry, Reports,
                                                   get_environment_var)

report_type = Reports.GREEN.value


app = dash.Dash(__name__)


def get_layout():
    directory = get_environment_var('JSON_FOLDER')
    language_options = ['All'] + [lang.lang_name for lang in Language]
    dropdown_options = report_type.get_report_dropdown_options(directory)
    selected_option = dropdown_options[0]['value'] if dropdown_options else None  # Set default value as the newest file generated

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
                    style={'marginRight': '20px', 'width': '15%'}
                ),
                dcc.Dropdown(
                    id='file-selector', maxHeight=1000,
                    options=dropdown_options,
                    value=selected_option,
                    clearable=False,
                    style={'width': '35%'}
                ),
                dcc.RadioItems(language_options, 'All', id='language-filter', inline=True, style={'width': '40%'}),
            ]
        ),

        # Container for dynamic content
        html.Div(id='report-content')
    ])


app.layout = get_layout


def create_table(fetcher: GithubFetcher, section: PackagesRegistry, language: str):
    header_row = html.Thead([
        html.Tr([
            html.Th('Package', rowSpan=3),
            html.Th('Clones', colSpan=5),
            html.Th('Visits', colSpan=5),
            html.Th('No of Forks', rowSpan=3),
            html.Th('No of Stars', rowSpan=3),
            html.Th('Watchers', rowSpan=3),
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
    packages: list[GithubPackage] = [item for item in fetcher.packages
                                     if item.package_site == section.repo_name and (language == 'All' or language == item.package_language)]  # type: ignore
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

    return html.Table(table_header + table_rows, id='downloads_table', style={
        'width': '98%',
        'borderCollapse': 'collapse',
    })


# Warning boxes for health score
def create_package_info_box(fetcher: GithubFetcher, section: PackagesRegistry, language: str):
    info_boxes = []
    packages: list[GithubPackage] = [item for item in fetcher.packages
                                     if item.package_site == section.repo_name and (language == 'All' or language == item.package_language)]  # type: ignore
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)

    for package in packages:
        info = package.analyse_package()
        if info:
            info_boxes.append(html.Div([
                html.H3(package.package_name),
                html.P(info),
            ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin': '10px'}))

    return html.Div(info_boxes)


def create_downloads_graph(fetcher: GithubFetcher, section: PackagesRegistry, language: str) -> Dict[str, Any]:
    packages: List[GithubPackage] = [item for item in fetcher.packages
                                     if item.package_site == section.repo_name and (language == 'All' or language == item.package_language)]  # type: ignore
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


def create_visits_graph(fetcher: GithubFetcher, section: PackagesRegistry, language: str) -> Dict[str, Any]:
    packages: list[GithubPackage] = [item for item in fetcher.packages
                                     if item.package_site == section.repo_name and (language == 'All' or language == item.package_language)]  # type: ignore
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
    [Input('file-selector', 'value'),
     Input('language-filter', 'value')]
)
def update_green_report(selected_file: str, selected_language: str):
    fetchers = {org: GithubFetcher.from_generated_file(selected_file, org.value) for org in EcosystemConfiguration}
    repo = PackagesRegistries.GITHUB
    return html.Div([
        dcc.Tabs(id="org-selector", children=[
            dcc.Tab(label=org.value.name, id=org.value.name, style={'font-weight': 'normal'},
                    selected_style={'font-weight': 'bold'}, children=[
                html.H1(f"{org.value.name} - {repo.name} Repositories Downloads {'' if selected_language == 'All' else ' - ' + selected_language}"),
                html.H2('Two Weeks Download Data Table'),
                create_table(fetchers[org], repo.value, selected_language),
                html.H2('Clones & Visits Trends'),
                html.Div([
                    dcc.Graph(
                        id='downloads-graph',
                        figure=create_downloads_graph(fetchers[org], repo.value, selected_language)
                    ),
                ], style={'display': 'inline-block', 'width': '48%'}),
                html.Div([
                    dcc.Graph(
                        id='visits-graph',
                        figure=create_visits_graph(fetchers[org], repo.value, selected_language)
                    ),
                ], style={'display': 'inline-block', 'width': '48%'}),
                html.H2('Health score warnings') if org.value.report_warnings else None,
                create_package_info_box(fetchers[org], repo.value, selected_language) if org.value.report_warnings else None,
            ])
            for org in EcosystemConfiguration
        ],
            colors={
            "border": "white",  # Border color
            "primary": "blue",  # Color of the selected tab
            "background": "lightgray"  # Color of the unselected tabs
        }),
    ])


if __name__ == '__main__':
    app.run_server(debug=False, port=report_type.repo_port, host='0.0.0.0')
