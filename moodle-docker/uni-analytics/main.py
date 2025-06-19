# Main inicial

import dash
from dash import html, dcc, Input, Output, State, ctx, no_update
from dashboards import dashboardGeral, dashboardAluno, dashboardProfessor, dashboardPre, dashboardPos
from forms import formularioMain, formularioPre, formularioPos  , formulariosAdmin
from db.uniAnalytics import init_uni_analytics_db
from db.uniAnalytics import connect_to_uni_analytics_db
from auth import login
from flask import Flask, session
from urllib.parse import urlparse, parse_qs 
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
    Input('url', 'pathname'),
    State('url', 'search') 
)
def display_page(pathname, search):
    print("Path recebido:", pathname)

    user_id = session.get("user_id")
    user_role = session.get("role")

    if not user_id or not user_role:
        return login.layout()

    course_id = 2  # Fixo por agora

    # Extrair item_id da query string (se existir)
    query_params = parse_qs(search[1:]) if search else {}
    item_id = int(query_params.get("item_id", [0])[0])  # Usa 0 por omissão

    if pathname in ["/", "/home"]:
        links_dash = []
        blocos_formularios = []

        # Dashboards
        if user_role != "admin":
            links_dash.append(dcc.Link("→ Dashboard Geral", href="/dashboards/dashboardGeral", className="btn-suave"))
        if user_role == "admin":
            links_dash.extend([
                dcc.Link("→ Administração de Formulários", href="/forms/formularioAdmin", className="btn-suave"),
                dcc.Link("→ Dashboard Pré-Avaliação", href="/dashboards/dashboardPre", className="btn-suave"),
                dcc.Link("→ Dashboard Pós-Avaliação", href="/dashboards/dashboardPos", className="btn-suave")
            ])
        elif user_role == "professor":
            links_dash.extend([
                dcc.Link("→ Dashboard Professor", href="/dashboards/dashboardProfessor", className="btn-suave"),
                dcc.Link("→ Dashboard Pré-Avaliação", href="/dashboards/dashboardPre", className="btn-suave"),
                dcc.Link("→ Dashboard Pós-Avaliação", href="/dashboards/dashboardPos", className="btn-suave")
            ])
        elif user_role == "aluno":
            links_dash = [
                dcc.Link("→ Dashboard Geral", href="/dashboards/dashboardGeral", className="btn-suave"),
                dcc.Link("→ Dashboard Aluno", href="/dashboards/dashboardAluno", className="btn-suave")
            ]
            # Verifica se pertence ao grupo "Avaliação Contínua"
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT group_name
                FROM course_data
                WHERE user_id = ?
                LIMIT 1
            """, (user_id,))
            resultado = cursor.fetchone()
            conn.close()

            if resultado and resultado[0] and "continua" in resultado[0].lower():
                links_dash.extend([
                    dcc.Link("→ Dashboard Pré-Avaliação", href="/dashboards/dashboardPre", className="btn-suave"),
                    dcc.Link("→ Dashboard Pós-Avaliação", href="/dashboards/dashboardPos", className="btn-suave")
                ])

            blocos_formularios = [formularioMain.listar_formularios_disponiveis(user_id)]

        # Verifica se existem formulários
        tem_formularios = len(blocos_formularios) > 0

        # Layout da página principal
        return html.Div([
            html.Div([
                html.Div("Bem-vindo ao Dashboard de Learning Analytics", className="dashboard-pre-titulo", style={"marginLeft": "250px"}),
            ], style={"marginTop": "30px"}),
        
            html.Div(
                className="linha-flex" if tem_formularios else "coluna-unica-central",
                children=[
                    html.Div(className="coluna-esquerda", children=[
                        html.Div(className="card", children=[
                            html.H3("Dashboards", className="home-bloco-titulo"),
                            html.Div(
                                style={"display": "flex", "flexDirection": "column", "gap": "10px"},
                                children=links_dash
                            )
                        ])
                    ])
                ] + (
                    [html.Div(className="coluna-direita", children=[
                        html.Div(className="card", children=blocos_formularios)
                    ])] if tem_formularios else []
                )
            )
        ])



    elif pathname == "/dashboards/dashboardGeral":
        return dashboardGeral.layout(user_id)
    
    elif pathname == "/dashboards/dashboardAluno":
        if user_role in ["aluno", "admin"]:
            return dashboardAluno.layout(user_id, course_id)
        return html.Div("Acesso não autorizado.")

    elif pathname == "/dashboards/dashboardProfessor":
        if user_role in ["professor", "admin"]:
            return dashboardProfessor.layout(user_id, course_id)
        return html.Div("Acesso não autorizado.")

    elif pathname == "/dashboards/dashboardPre":
        if user_role in ["professor", "admin", "aluno"]:
            return dashboardPre.layout()
        return html.Div("Acesso não autorizado.")

    elif pathname == "/dashboards/dashboardPos":
        if user_role in ["professor", "admin", "aluno"]:
            return dashboardPos.layout()
        return html.Div("Acesso não autorizado.")

    elif pathname.startswith("/forms/"):
        if user_role in ["aluno" ,"admin"]:
            return formularioMain.get_layout(pathname, user_id, item_id) or html.Div("Formulário não encontrado.")
        return html.Div("Acesso não autorizado.")

    return html.Div("Página não encontrada.")

# Arranque da aplicação
if __name__ == '__main__':
    dashboardGeral.register_callbacks(app)
    login.register_callbacks(app)
    formulariosAdmin.register_callbacks(app)
    formularioPre.register_callbacks(app)
    formularioPos.register_callbacks(app)
    dashboardPre.register_callbacks(app)
    dashboardPos.register_callbacks(app)
    app.run(debug=True, host="0.0.0.0", port=8050)