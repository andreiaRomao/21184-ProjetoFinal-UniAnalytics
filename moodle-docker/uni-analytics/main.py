import dash
from dash import html, dcc
from dashboards import dashboardGeral, dashboardAluno, dashboardProfessor
from forms import formularioMain  # ← Lógica que decide qual formulário mostrar
from db.uniAnalytics import init_uni_analytics_db  # ← Função para criar a DB/tabela se não existir

# Inicializar tabela da base de dados (se necessário)
print("A inicializar a base de dados...")
init_uni_analytics_db()
print("Base de dados pronta.")

# App Dash
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
    print("Path recebido:", pathname)

    aluno_id = 105
    course_id = 2
    professor_id = 2

    if pathname == "/" or pathname == "/home":
        return html.Div([
            html.H1("Bem-vindo ao Dashboard de Learning Analytics"),
            html.Div([
                dcc.Link("→ Dashboard Geral", href="/dashboards/dashboardGeral", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Dashboard Aluno", href="/dashboards/dashboardAluno", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Dashboard Professor", href="/dashboards/dashboardProfessor", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Inquérito Pré-Avaliação", href="/forms/formularioPre", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Inquérito Pós-Avaliação", href="/forms/formularioPos", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Administração de Formulários", href="/forms/formularioAdmin", style={"display": "block", "margin": "10px"})
            ])
        ])
    elif pathname == "/dashboards/dashboardGeral":
        return dashboardGeral.layout()
    elif pathname == "/dashboards/dashboardAluno":
        return dashboardAluno.layout(aluno_id, course_id)
    elif pathname == "/dashboards/dashboardProfessor":
        return dashboardProfessor.layout(professor_id, course_id)

    # Verifica se é um formulário e retorna o layout correspondente
    form_layout = formularioMain.get_layout(pathname)
    if form_layout:
        return form_layout

    return html.Div("Página não encontrada")

if __name__ == '__main__':
    formularioMain.register_callbacks(app)  # ← Regista todos os callbacks
    dashboardGeral.register_callbacks(app) # ← Regista callbacks do dashboard geral
    app.run(debug=True, host="0.0.0.0", port=8050)