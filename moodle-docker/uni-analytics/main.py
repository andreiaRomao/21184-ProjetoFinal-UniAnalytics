import dash
from dash import html, dcc, Input, Output, State, ctx, no_update
from dashboards import dashboardGeral, dashboardAluno, dashboardProfessor
from forms import formularioMain  
from db.uniAnalytics import init_uni_analytics_db 
from auth import login
from flask import Flask, session
import os
import secrets

# Inicializar a base de dados (caso necessário)
print("A inicializar a base de dados...")
init_uni_analytics_db()
print("Base de dados pronta.")

# Instanciar aplicação Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Learning Analytics"
server = app.server

# Definir chave secreta para gestão de sessão
server.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

# Layout principal (contém sempre o botão de logout e o componente de redirecionamento)
app.layout = html.Div([
    dcc.Location(id='url'),
    dcc.Store(id='login-state', storage_type='session'),
    dcc.Location(id='logout-url', refresh=True),
    html.Button("Terminar Sessão", id="logout-button", className="logout-btn"),
    html.Div(id='page-content')
])

# Redirecionar após login/registo
@app.callback(
    Output('url', 'pathname'),
    Output('login-state', 'clear_data'),
    Input('login-state', 'data'),
    prevent_initial_call=True
)
def redirect_after_login(data):
    if data and 'redirect' in data:
        return data['redirect'], True
    return dash.no_update, False

# Mostrar/ocultar botão de logout com base na sessão
@app.callback(
    Output("logout-button", "style"),
    Input("url", "pathname")
)
def toggle_logout_visibility(pathname):
    if session.get("user_id") and session.get("role"):
        return {"display": "block", "margin": "10px"}
    return {"display": "none"}

# Executar logout
@app.callback(
    Output("logout-url", "pathname"),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True
)
def logout_user(n_clicks):
    session.clear()
    return "/"

# Callback principal de navegação
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    print("Path recebido:", pathname)

    user_id = session.get("user_id")
    user_role = session.get("role")

    if not user_id or not user_role:
        return login.layout()

    course_id = 2  # Fixo por agora

    if pathname in ["/", "/home"]:
        links = []

        if user_role == "admin":
            links.extend([
                dcc.Link("→ Dashboard Professor", href="/dashboards/dashboardProfessor", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Dashboard Aluno", href="/dashboards/dashboardAluno", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Administração de Formulários", href="/forms/formularioAdmin", style={"display": "block", "margin": "10px"})
            ])
        elif user_role == "professor":
            links.append(dcc.Link("→ Dashboard Professor", href="/dashboards/dashboardProfessor", style={"display": "block", "margin": "10px"}))
        elif user_role == "aluno":
            links.extend([
                dcc.Link("→ Dashboard Aluno", href="/dashboards/dashboardAluno", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Inquérito Pré-Avaliação", href="/forms/formularioPre", style={"display": "block", "margin": "10px"}),
                dcc.Link("→ Inquérito Pós-Avaliação", href="/forms/formularioPos", style={"display": "block", "margin": "10px"})
            ])

        return html.Div([
            html.H1("Bem-vindo ao Dashboard de Learning Analytics"),
            html.Div(links)
        ])

    elif pathname == "/dashboards/dashboardAluno":
        if user_role in ["aluno", "admin"]:
            return dashboardAluno.layout(user_id, course_id)
        return html.Div("Acesso não autorizado.")

    elif pathname == "/dashboards/dashboardProfessor":
        if user_role in ["professor", "admin"]:
            return dashboardProfessor.layout(user_id, course_id)
        return html.Div("Acesso não autorizado.")

    elif pathname.startswith("/forms/"):
        if user_role in ["aluno", "admin"]:
            form_layout = formularioMain.get_layout(pathname)
            return form_layout if form_layout else html.Div("Formulário não encontrado.")
        return html.Div("Acesso não autorizado.")

    return html.Div("Página não encontrada.")

# Arranque da aplicação
if __name__ == '__main__':
    formularioMain.register_callbacks(app)
    dashboardGeral.register_callbacks(app)
    login.register_callbacks(app)
    app.run(debug=True, host="0.0.0.0", port=8050)