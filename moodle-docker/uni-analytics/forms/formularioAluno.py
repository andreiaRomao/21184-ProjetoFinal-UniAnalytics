from dash import html, dcc, Input, Output, State
import dash
from db.formsDatabase import connect_to_forms_db

def layout():
    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            html.H2("Inquérito de Satisfação", className="card-title"),
            dcc.Store(id='etapa', data=1),
            dcc.Store(id='respostas', data={}),
            
            html.Div(id='pergunta-area'),

            html.Br(),
            html.Div([
                html.Button("Seguinte", id="next-btn", n_clicks=0, className="btn"),
                html.Button("Submeter", id="submit-btn", n_clicks=0, className="btn", style={"display": "none"}),
                html.Button("Ver Resultados", id="ver-resultados-btn", n_clicks=0, className="btn", style={"marginTop": "20px"}),
                html.Div(id="resultados-db", style={"marginTop": "20px"})

            ], style={"display": "flex", "gap": "20px"}),

            html.Div(id="mensagem-final", style={"marginTop": "20px", "fontWeight": "bold", "textAlign": "center"})
        ])
    ])

def register_callbacks(app):
    perguntas = {
        1: "O conteúdo foi claro?",
        2: "Recomendarias esta disciplina?"
    }

    opcoes = {
        1: ["Sim", "Não"],
        2: ["Sim", "Talvez", "Não"]
    }

    # Renderiza a pergunta atual
    @app.callback(
        Output("pergunta-area", "children"),
        Output("next-btn", "style"),
        Output("submit-btn", "style"),
        Input("etapa", "data"),
        State("respostas", "data")
    )
    def mostrar_pergunta(etapa, respostas):
        if etapa > len(perguntas):
            return html.Div("Obrigado! A submeter..."), {"display": "none"}, {"display": "inline-block"}

        return html.Div([
            html.Label(perguntas[etapa]),
            dcc.Dropdown(
                id="resposta-atual",
                options=[{"label": o, "value": o} for o in opcoes[etapa]],
                placeholder="Seleciona uma opção",
                value=respostas.get(str(etapa))
            )
        ]), {"display": "inline-block"}, {"display": "none"}

    # Avança para a próxima etapa guardando a resposta
    @app.callback(
        Output("etapa", "data"),
        Output("respostas", "data"),
        Input("next-btn", "n_clicks"),
        State("etapa", "data"),
        State("respostas", "data"),
        State("resposta-atual", "value"),
        prevent_initial_call=True
    )
    def avancar(n_clicks, etapa, respostas, resposta):
        if resposta:
            respostas[str(etapa)] = resposta
            return etapa + 1, respostas
        return etapa, respostas

    # Submete as respostas para a base de dados
    @app.callback(
        Output("mensagem-final", "children"),
        Input("submit-btn", "n_clicks"),
        State("respostas", "data"),
        prevent_initial_call=True
    )
    def submeter(n, respostas):
        if "1" not in respostas or "2" not in respostas:
            return "Por favor responde a todas as perguntas."
        
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO respostas (pergunta, resposta) VALUES (?, ?)", ("O conteúdo foi claro?", respostas["1"]))
            cursor.execute("INSERT INTO respostas (pergunta, resposta) VALUES (?, ?)", ("Recomendarias esta disciplina?", respostas["2"]))
            conn.commit()
            conn.close()
            return "Obrigado! Respostas submetidas com sucesso."
        except Exception as e:
            return f"Erro ao guardar: {str(e)}"

    @app.callback(
        Output("resultados-db", "children"),
        Input("ver-resultados-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def mostrar_resultados(n_clicks):
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("SELECT pergunta, resposta, timestamp FROM respostas ORDER BY timestamp DESC")
            registos = cursor.fetchall()
            conn.close()

            if not registos:
                return html.Div("Ainda não existem respostas registadas.")

            return html.Div([
                html.H4("Respostas Submetidas:"),
                html.Ul([
                    html.Li(f"{pergunta} → {resposta} ({timestamp})")
                    for pergunta, resposta, timestamp in registos
                ])
            ])
        except Exception as e:
            return html.Div(f"Erro ao ler da base de dados: {str(e)}")
