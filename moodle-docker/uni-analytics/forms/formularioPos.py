from dash import html, dcc, Input, Output, State
from db.formsDatabase import connect_to_forms_db

def layout():
    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            html.H2("Pós-Avaliação da Disciplina", className="card-title"),
            dcc.Store(id='etapa-pos', data=1),
            dcc.Store(id='respostas-pos', data={}),

            html.Div(id='pergunta-area-pos'),

            html.Br(),
            html.Div([
                html.Button("Seguinte", id="next-btn-pos", n_clicks=0, className="btn"),
                html.Button("Submeter", id="submit-btn-pos", n_clicks=0, className="btn", style={"display": "none"}),
                html.Button("Ver Resultados", id="ver-resultados-btn-pos", n_clicks=0, className="btn", style={"marginTop": "20px"}),
            ], style={"display": "flex", "gap": "20px"}),

            html.Div(id="mensagem-final-pos", style={"marginTop": "20px", "fontWeight": "bold", "textAlign": "center"}),
            html.Div(id="resultados-db-pos", style={"marginTop": "20px"})
        ])
    ])

def register_callbacks(app):
    perguntas = {
        1: "Como avalias a tua aprendizagem global?",
        2: "Sentiste-te preparado para o exame final?",
        3: "A disciplina superou as tuas expectativas?"
    }

    opcoes = {
        1: ["Muito boa", "Boa", "Razoável", "Fraca"],
        2: ["Sim", "Não", "Mais ou menos"],
        3: ["Sim", "Não"]
    }

    @app.callback(
        Output("pergunta-area-pos", "children"),
        Output("next-btn-pos", "style"),
        Output("submit-btn-pos", "style"),
        Input("etapa-pos", "data"),
        State("respostas-pos", "data")
    )
    def mostrar_pergunta(etapa, respostas):
        if etapa > len(perguntas):
            return html.Div("Obrigado! A submeter..."), {"display": "none"}, {"display": "inline-block"}

        return html.Div([
            html.Label(perguntas[etapa]),
            dcc.Dropdown(
                id="resposta-pos",
                options=[{"label": o, "value": o} for o in opcoes[etapa]],
                placeholder="Seleciona uma opção",
                value=respostas.get(str(etapa))
            )
        ]), {"display": "inline-block"}, {"display": "none"}

    @app.callback(
        Output("etapa-pos", "data"),
        Output("respostas-pos", "data"),
        Input("next-btn-pos", "n_clicks"),
        State("etapa-pos", "data"),
        State("respostas-pos", "data"),
        State("resposta-pos", "value"),
        prevent_initial_call=True
    )
    def avancar(n_clicks, etapa, respostas, resposta_atual):
        if resposta_atual:
            respostas[str(etapa)] = resposta_atual
            return etapa + 1, respostas
        return etapa, respostas

    @app.callback(
        Output("mensagem-final-pos", "children"),
        Input("submit-btn-pos", "n_clicks"),
        State("respostas-pos", "data"),
        prevent_initial_call=True
    )
    def submeter(n, respostas):
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            for key, resposta in respostas.items():
                pergunta_texto = perguntas[int(key)]
                cursor.execute("INSERT INTO respostas (pergunta, resposta, tipo_formulario) VALUES (?, ?, ?)", (pergunta_texto, resposta, "pos"))
            conn.commit()
            conn.close()
            return "Obrigado! Respostas submetidas com sucesso."
        except Exception as e:
            return f"Erro ao guardar: {str(e)}"

    @app.callback(
        Output("resultados-db-pos", "children"),
        Input("ver-resultados-btn-pos", "n_clicks"),
        prevent_initial_call=True
    )
    def ver_resultados(n):
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("SELECT pergunta, resposta, timestamp FROM respostas WHERE tipo_formulario = 'pos' ORDER BY timestamp DESC LIMIT 10")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return "Ainda não existem respostas registadas."

            return html.Ul([
                html.Li(f"{pergunta} → {resposta} ({ts})") for pergunta, resposta, ts in rows
            ])
        except Exception as e:
            return f"Erro ao obter resultados: {str(e)}"