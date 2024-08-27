from datetime import datetime, timedelta
import os
import glob
from typing import Any, Dict
import dash
from dash import dcc, html, Input, Output
# from dash import dash_table
import plotly.graph_objs as go
from fetch_data import DownloadsFetcher, PackageDownloads
from utils import Repository

app = dash.Dash(__name__)

directory = './Output'
json_files = glob.glob(os.path.join(directory, 'blue*.json'))
json_files.sort(reverse=True)

dropdown_options = [{'label': os.path.basename(file), 'value': file} for file in json_files]

# Layout of the Dash app
app.layout = html.Div(children=[
    dcc.Dropdown(
        id='file-selector',
        options=dropdown_options,
        value=dropdown_options[0]['value'],  # Set default value as the first file
        clearable=False
    ),

    # Container for dynamic content
    html.Div(id='report-content')
])


def create_table(fetcher: DownloadsFetcher, section: Repository):
    header_row = [html.Th("Package"), html.Th("Downloads last month"), html.Th("Downloads last week"),
                  html.Th("Avg downloads per day"), html.Th("Libraries.io Score"), html.Th("Site Score")]
    table_header = [html.Tr(header_row)]
    table_rows = []
    packages: list[PackageDownloads] = [item for item in fetcher.downloads if item.package_site == section.repo_name]
    packages.sort(key=lambda pkg: pkg.no_of_downloads, reverse=True)
    for package in packages:
        package_statistics = package.calculate_monthly_statistics_from_daily_downloads(fetcher.end_date)
        row = [
            html.Td(package.package_name),
            html.Td(package_statistics['last_month_downloads']),
            html.Td(package_statistics['last_week_downloads']),
            html.Td(int(package_statistics['avg_daily_downloads'])),
            html.Td(package_statistics['libraries_io_score'])
        ]
        if (package.site_score):
            row.extend([html.Td(f"{package.site_score['final']:.2f}")])
            #row.extend([html.Td(item) for item in package.site_score.get('detail',{})])
        table_rows.append(html.Tr(row))

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


@app.callback(
    Output('report-content', 'children'),
    Input('file-selector', 'value')
)
def update_report(selected_file: str):
    fetcher = DownloadsFetcher.from_json_file(selected_file)
    return html.Div([
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
