import dash
from dash import html, dcc
from dashboards import dashboardGeral, dashboardAluno, dashboardProfessor
from forms import formularioAluno

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Learning Analytics"
server = app.server

app.layout = html.Div([
    dcc.Location(id='url'),
    html.Div(id='page-content')
])

@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')]
)
def display_page(pathname):
    print("Path recebido:", pathname)  # Para diagnóstico no terminal
    # Valores fixos temporários para simulação
    aluno_id = 105
    course_id = 2

    if pathname == "/" or pathname == "/home":
        return html.Div([
            html.H1("Bem-vindo ao Dashboard de Learning Analytics"),
            html.Div([
                dcc.Link("→ Dashboard Geral", href="/dashboards/dashboardGeral", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Dashboard Aluno", href="/dashboards/dashboardAluno", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Dashboard Professor", href="/dashboards/dashboardProfessor", style={"display": "block", "margin": "10px"})
            ])
        ])
    elif pathname == "/dashboards/dashboardGeral":
        return dashboardGeral.layout()
    elif pathname == "/dashboards/dashboardAluno":
        return dashboardAluno.layout(aluno_id, course_id)
    elif pathname == "/dashboards/dashboardProfessor":
        return dashboardProfessor.layout()
    elif pathname == "/forms/formularioAluno":
        return formularioAluno.layout()
    return html.Div("Página não encontrada")


if __name__ == '__main__':
    formularioAluno.register_callbacks(app)
    app.run(debug=True, host="0.0.0.0", port=8050)