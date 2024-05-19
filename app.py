from dash import html, dcc, Input, Output, Dash
import pandas as pd
import sqlalchemy
from dash.dash_table import DataTable
from flask import Flask

server = Flask(__name__)
server.config['SECRET_KEY'] = 'your-secret-key'
server.config['SESSION_COOKIE_SECURE'] = True
app = Dash(__name__, server=server, external_stylesheets=['https://cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css'])

engine = sqlalchemy.create_engine('postgresql://user:password@db:5432/mydatabase')


# обновите функцию load_data, чтобы она принимала аргумент weighted
def load_data(weighted=False):
    query = """
    SELECT s.name as student_name, p.name as opportunity_name, pr.value as score, p.weight as weight
    FROM students s
    JOIN performance_records pr ON s.student_id = pr.student_id
    JOIN performance_opportunities p ON pr.opportunity_id = p.opportunity_id;
    """
    df = pd.read_sql(query, engine)
    if weighted:
        df['score'] *= df['weight']
    pivot_df = df.pivot(index='student_name', columns='opportunity_name', values='score')
    pivot_df.reset_index(inplace=True) #
    return pivot_df

app.layout = html.Div(children=[
    dcc.RadioItems(
        id='switch',
        options=[
            {'label': 'Показывать баллы за задание', 'value': 'values'},
            {'label': 'Показывать баллы для модеуса', 'value': 'weighted'}
        ],
        value='values'
    ),
    html.H1(children='Пользовательский дашборд'),

    html.Button('Обновить данные', id='refresh-button', n_clicks=0),

    DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in load_data().columns],
        data=load_data().to_dict('records'),
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_cell={
            'textAlign': 'left',
            'minWidth': '100px', 'width': '100px', 'maxWidth': '100px',
            'whiteSpace': 'normal'
        }
    )
])

@app.callback(
    Output('table', 'data'),
    [Input('refresh-button', 'n_clicks'),
     Input('switch', 'value')]
)
def update_table(n_clicks, switch_value):
    df = load_data(weighted=(switch_value == 'weighted'))
    return df.to_dict('records')

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)