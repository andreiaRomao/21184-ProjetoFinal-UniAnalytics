from dash import html, dcc, Input, Output, State
import dash
from db.formsDatabase import connect_to_forms_db

def layout():
    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            html.H2("Pré-Avaliação", className="card-title"),
            dcc.Store(id='etapa-pre', data=1),
            dcc.Store(id='respostas-pre', data={}),

            html.Div(id='pergunta-area-pre'),

            html.Br(),
            html.Div([
                html.Button("Seguinte", id="next-btn-pre", n_clicks=0, className="btn"),
                html.Button("Submeter", id="submit-btn-pre", n_clicks=0, className="btn", style={"display": "none"}),
                html.Button("Ver Resultados", id="ver-resultados-btn-pre", n_clicks=0, className="btn"),
            ], style={"display": "flex", "gap": "20px"}),

            html.Div(id="mensagem-final-pre", style={"marginTop": "20px", "fontWeight": "bold", "textAlign": "center"}),
            html.Div(id="resultados-db-pre", style={"marginTop": "20px"})
        ])
    ])

def register_callbacks(app):
    perguntas = {
        1: "Tens expectativas positivas para esta disciplina?",
        2: "Sentes-te preparado para os temas que vão ser abordados?"
    }

    opcoes = {
        1: ["Sim", "Não"],
        2: ["Sim", "Talvez", "Não"]
    }

    # Mostra a pergunta atual
    @app.callback(
        Output("pergunta-area-pre", "children"),
        Output("next-btn-pre", "style"),
        Output("submit-btn-pre", "style"),
        Input("etapa-pre", "data"),
        State("respostas-pre", "data")
    )
    def mostrar_pergunta(etapa, respostas):
        if etapa > len(perguntas):
            return html.Div("Obrigado! A submeter..."), {"display": "none"}, {"display": "inline-block"}

        return html.Div([
            html.Label(perguntas[etapa]),
            dcc.Dropdown(
                id="resposta-pre",
                options=[{"label": o, "value": o} for o in opcoes[etapa]],
                placeholder="Seleciona uma opção",
                value=respostas.get(str(etapa))
            )
        ]), {"display": "inline-block"}, {"display": "none"}

    # Guarda a resposta atual e avança
    @app.callback(
        Output("etapa-pre", "data"),
        Output("respostas-pre", "data"),
        Input("next-btn-pre", "n_clicks"),
        State("etapa-pre", "data"),
        State("respostas-pre", "data"),
        State("resposta-pre", "value"),
        prevent_initial_call=True
    )
    def avancar(n_clicks, etapa, respostas, resposta_atual):
        if resposta_atual:
            respostas[str(etapa)] = resposta_atual
            return etapa + 1, respostas
        return etapa, respostas

    # Submeter para base de dados
    @app.callback(
        Output("mensagem-final-pre", "children"),
        Input("submit-btn-pre", "n_clicks"),
        State("respostas-pre", "data"),
        prevent_initial_call=True
    )
    def submeter(n, respostas):
        if len(respostas) < len(perguntas):
            return "Por favor responde a todas as perguntas."

        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            for idx, pergunta in perguntas.items():
                cursor.execute(
                    "INSERT INTO respostas (pergunta, resposta, tipo_formulario) VALUES (?, ?, ?)",
                    (pergunta, respostas[str(idx)], "pre")
                )
            conn.commit()
            conn.close()
            return "Obrigado! Respostas submetidas com sucesso."
        except Exception as e:
            return f"Erro ao guardar: {str(e)}"

    # Mostrar resultados
    @app.callback(
        Output("resultados-db-pre", "children"),
        Input("ver-resultados-btn-pre", "n_clicks"),
        prevent_initial_call=True
    )
    def ver_resultados(n_clicks):
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("SELECT pergunta, resposta, timestamp FROM respostas WHERE tipo_formulario = 'pre' ORDER BY timestamp DESC LIMIT 10")
            rows = cursor.fetchall()
            conn.close()

            return html.Ul([
                html.Li(f"{r[2]} - {r[0]} → {r[1]}") for r in rows
            ])
        except Exception as e:
            return f"Erro ao ler base de dados: {str(e)}"
