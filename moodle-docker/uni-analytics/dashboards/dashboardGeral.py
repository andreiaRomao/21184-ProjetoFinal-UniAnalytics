from dash import html, dcc
import plotly.express as px
from queries.queriesGeral import fetch_user_course_data

def layout():
    try:
        df = fetch_user_course_data()
    except Exception as e:
        print("Erro ao buscar dados da BD:", e)
        return html.Div("Erro ao ligar à base de dados.")

    fig = px.bar(
        df, x="curso", y="total_alunos", text="total_alunos",
        title="Total de alunos por curso", labels={"total_alunos": "Total de Alunos"}
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff"
    )

    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            html.H1("Dashboard Moodle", className="card-title"),
            dcc.Graph(figure=fig)
        ])
    ])
