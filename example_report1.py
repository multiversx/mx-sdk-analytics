from dash import Dash, dcc, html
import plotly.graph_objs as go

data = {
    "package1": [
        {"date": "2023-08-01", "downloads": 135},
        {"date": "2023-08-02", "downloads": 136},
        {"date": "2023-08-03", "downloads": 220},
        {"date": "2023-08-04", "downloads": 169},
        {"date": "2023-08-05", "downloads": 44},
        {"date": "2023-08-06", "downloads": 35}
    ],
    "package2": [
        {"date": "2023-08-01", "downloads": 1251},
        {"date": "2023-08-02", "downloads": 1593},
        {"date": "2023-08-03", "downloads": 1530},
        {"date": "2023-08-04", "downloads": 1180},
        {"date": "2023-08-05", "downloads": 64},
        {"date": "2023-08-06", "downloads": 111}
    ]
}

app = Dash(__name__)

def create_table(data):
    table_header = [html.Tr([html.Th("Date"), html.Th("Package 1 Downloads"), html.Th("Package 2 Downloads")])]
    
    table_rows = []
    for i in range(len(data["package1"])):
        row = html.Tr([
            html.Td(data["package1"][i]["date"]),
            html.Td(data["package1"][i]["downloads"]),
            html.Td(data["package2"][i]["downloads"])
        ])
        table_rows.append(row)
    
    return html.Table(table_header + table_rows)

def create_graph(data):
    traces = [
        go.Scatter(
            x=[entry['date'] for entry in data['package1']],
            y=[entry['downloads'] for entry in data['package1']],
            mode='lines+markers',
            name='Package 1'
        ),
        go.Scatter(
            x=[entry['date'] for entry in data['package2']],
            y=[entry['downloads'] for entry in data['package2']],
            mode='lines+markers',
            name='Package 2'
        )
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
    html.H1("NPM Package Downloads"),
    
    html.H2("Download Data Table"),
    create_table(data),
    
    html.H2("Download Trends"),
    dcc.Graph(
        id='downloads-graph',
        figure=create_graph(data)
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
