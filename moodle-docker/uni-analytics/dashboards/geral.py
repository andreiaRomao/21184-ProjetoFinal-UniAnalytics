import dash
from dash import dcc, html
import plotly.express as px

def create_dashboard(df):
    fig = px.bar(df, x="curso", y="total_alunos", title="Total de alunos por curso")
    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.H1("Dashboard Moodle"),
        dcc.Graph(figure=fig)
    ])
    app.run(debug=True, host="0.0.0.0", port=8050)
