import asyncio
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import dash
import plotly.graph_objs as go
from constants import GREEN_REPORT_PORT
from dash import Input, Output, dcc, html
from dash.dependencies import State
from dotenv.main import load_dotenv
from github_fetcher import GithubFetcher, GithubPackage
from utils import FormattedDate, Language, PackagesRegistry, get_environmen_var

from multiversx_usage_analytics_tool.ecosystem_configuration import \
    EcosystemConfiguration
from multiversx_usage_analytics_tool.green_report_to_pdf import \
    export_dash_report_to_pdf

load_dotenv()

app = dash.Dash(__name__)
background_color = '#e6ffe6'
directory = get_environmen_var('JSON_FOLDER')
report_directory = get_environmen_var('REPORT_FOLDER')

json_files = sorted(Path(directory).glob('green*.json'), reverse=True)
dropdown_options = [{'label': file.name, 'value': str(file)} for file in json_files]
language_options = ['All'] + [lang.lang_name for lang in Language]
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
                id='file-selector', maxHeight=1000,
                options=dropdown_options,
                value=dropdown_options[0]['value'],  # Set default value as the newest file generated
                clearable=False,
                style={'width': '35%'}
            ),
            dcc.RadioItems(language_options, 'All', id='language-filter', inline=True, style={'width': '40%'}),
            dcc.ConfirmDialog(id='confirm-dialog', message=f'The PDF has been saved successfully. \nFolder: {report_directory}'),
            dcc.Loading(
                id="loading",
                type="default",
                children=html.Div(id='loading-output', hidden=True),
                fullscreen=True,
                style={"backgroundColor": "rgba(0, 0, 0, 0.5)"},
            ),
            html.Button('Save PDF', id='save-pdf-button'),
        ]
    ),

    # Container for dynamic content
    html.Div(id='report-content')
])


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

    return html.Table(table_header + table_rows, style={
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
    repo = PackagesRegistry.GITHUB
    return html.Div([
        dcc.Tabs(id="org-selector", children=[
            dcc.Tab(label=org.value.name, id=org.value.name, style={'font-weight': 'normal'},
                    selected_style={'font-weight': 'bold'}, children=[
                html.H1(f"{org.value.name} - {repo.name} Repositories Downloads {'' if selected_language == 'All' else ' - ' + selected_language}"),
                html.H2('Two Weeks Download Data Table'),
                create_table(fetchers[org], repo, selected_language),
                html.H2('Clones & Visits Trends'),
                html.Div([
                    dcc.Graph(
                        id='downloads-graph',
                        figure=create_downloads_graph(fetchers[org], repo, selected_language)
                    ),
                ], style={'display': 'inline-block', 'width': '48%'}),
                html.Div([
                    dcc.Graph(
                        id='visits-graph',
                        figure=create_visits_graph(fetchers[org], repo, selected_language)
                    ),
                ], style={'display': 'inline-block', 'width': '48%'}),
                html.H2('Health score warnings'),
                create_package_info_box(fetchers[org], repo, selected_language)
            ])
            for org in EcosystemConfiguration
        ],
            colors={
            "border": "white",  # Border color
            "primary": "blue",  # Color of the selected tab
            "background": "lightgray"  # Color of the unselected tabs
        }),
    ])


def save_pdf(selected_file: str):
    global message
    message = ''
    loop = asyncio.new_event_loop()  # Create a new event loop
    asyncio.set_event_loop(loop)
    loop.run_until_complete(export_dash_report_to_pdf(selected_file))
    message = 'done'


selected_file: str


@app.callback(
    Output('loading-output', 'children'),
    Input('save-pdf-button', 'n_clicks'),
    State('file-selector', 'value'),
    prevent_initial_call=True
)
def trigger_pdf_generation(n_clicks: int, selected_file: str):
    if n_clicks:
        threading.Thread(target=save_pdf, args=(selected_file,)).start()
        while message != 'done':
            time.sleep(1)
        return "Generating PDF..."
    return ""


@app.callback(
    Output('confirm-dialog', 'displayed'),
    Input('loading-output', 'children'),
    prevent_initial_call=True
)
def display_dialog_after_pdf(saved_message: str):
    if saved_message == "Generating PDF...":
        return True
    return False


if __name__ == '__main__':
    app.run_server(debug=False, port=GREEN_REPORT_PORT, host='0.0.0.0')
