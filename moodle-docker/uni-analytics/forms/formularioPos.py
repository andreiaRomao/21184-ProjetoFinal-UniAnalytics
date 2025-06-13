import dash
from dash import html, dcc, Input, State, Output
from dash import ALL
from dash.exceptions import PreventUpdate
from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger

# Layout da página de formulário de Pós-Avaliação
def layout(user_id):
    logger.info(f"[POS] Aluno com ID {user_id} acedeu ao formulário de pós-avaliação")
    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            dcc.Interval(id="init-load-pos", interval=1, n_intervals=0, max_intervals=1),
            html.H2("Pós-Avaliação", className="card-title"),

            dcc.Store(id='etapa-pos', data=0),          # Etapa atual (0 = introdução)
            dcc.Store(id='respostas-pos', data={}),     # Respostas dadas até ao momento
            dcc.Store(id='perguntas-pos'),              # Perguntas carregadas do banco de dados
            dcc.Store(id="aluno-id", data=user_id),     # Valor dinâmico vindo da sessão

            html.Div(id='pergunta-area-pos', children="A carregar perguntas..."),

            html.Br(),

            html.Div([
                html.Button("Anterior", id="back-btn-pos", n_clicks=0, className="btn"),
                html.Button("Seguinte", id="next-btn-pos", n_clicks=0, className="btn"),
                html.Button("Submeter", id="submit-btn-pos", n_clicks=0, className="btn", style={"display": "none"}),
                html.Button("Ver Resultados", id="ver-resultados-btn-pos", n_clicks=0, className="btn")
            ], style={
                "display": "flex",
                "gap": "20px",
                "justifyContent": "center",
                "width": "100%"
            }),

            html.Div(id="mensagem-final-pos", style={"marginTop": "20px", "fontWeight": "bold", "textAlign": "center"}),

            html.Div(id="resultados-db-pos", style={"marginTop": "20px"})
        ])
    ])

# Callbacks para o formulário de Pós-Avaliação
def register_callbacks(app):

    @app.callback(
        Output("perguntas-pos", "data"),
        Input("init-load-pos", "n_intervals")
    )
    def carregar_perguntas(n):
        logger.debug(f"[POS] Iniciar carregamento de perguntas com n_intervals={n}")
        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            query = """
                SELECT id, question
                FROM forms_questions
                WHERE form_type = 'pos'
                ORDER BY id ASC
            """
            logger.debug(f"[POS] Executar query: {query.strip()}")
            cursor.execute(query)
            perguntas = cursor.fetchall()
            conn.close()
            logger.info(f"[POS] Carregadas {len(perguntas)} perguntas.")
            return [{"id": p[0], "texto": p[1]} for p in perguntas]
        except Exception as e:
            logger.exception("[POS] Erro ao carregar perguntas")
            return []

    @app.callback(
        Output("pergunta-area-pos", "children"),
        Output("next-btn-pos", "style"),
        Output("submit-btn-pos", "style"),
        Output("back-btn-pos", "style"),
        Input("etapa-pos", "data"),
        Input("perguntas-pos", "data"),
        State("respostas-pos", "data")
    )
    def mostrar_pergunta(etapa, perguntas, respostas):
        if perguntas is None:
            raise PreventUpdate

        if etapa == 0:
            return html.Div(
                "Bem-vindo ao formulário de pós-avaliação. As seguintes perguntas servem apenas para fins estatísticos e não serão associadas à tua identidade.",
                className="pergunta-card"
            ), {"display": "inline-block"}, {"display": "none"}, {"display": "none"}

        if etapa == len(perguntas) + 1:
            return html.Div(
                "Obrigado! As tuas respostas vão ser submetidas.",
                className="pergunta-card"
            ), {"display": "none"}, {"display": "none"}, {"display": "none"}

        if etapa == len(perguntas):
            return html.Div(
                "Confirmação: Estás prestes a submeter as tuas respostas.",
                className="pergunta-card"
            ), {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"}

        pergunta_atual = perguntas[etapa - 1]
        pergunta_id = pergunta_atual["id"]

        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            query = "SELECT id, answer FROM forms_answers WHERE question_id = ?"
            cursor.execute(query, (pergunta_id,))
            rows = cursor.fetchall()
            conn.close()
            opcoes = [{"label": r[1], "value": r[0]} for r in rows]
        except Exception as e:
            logger.exception("[POS] Erro ao carregar opções")
            opcoes = []

        return html.Div([
            html.Label(pergunta_atual["texto"]),
            dcc.Dropdown(
                id={"type": "resposta-pos", "index": etapa},
                options=opcoes,
                className="pergunta-opcao",
                placeholder="Seleciona uma opção",
                value=respostas.get(str(pergunta_id))
            )
        ], className="pergunta-card"), {"display": "inline-block"}, {"display": "none"}, {"display": "inline-block" if etapa > 1 else "none"}

    @app.callback(
        Output("etapa-pos", "data"),
        Output("respostas-pos", "data"),
        Input("next-btn-pos", "n_clicks"),
        Input("back-btn-pos", "n_clicks"),
        State("etapa-pos", "data"),
        State("respostas-pos", "data"),
        State({"type": "resposta-pos", "index": ALL}, "value"),
        State("perguntas-pos", "data"),
        prevent_initial_call=True
    )
    def navegar(n_seguinte, n_anterior, etapa_atual, respostas, resposta_atual_lista, perguntas):
        ctx = dash.callback_context

        if not ctx.triggered or perguntas is None:
            raise PreventUpdate

        botao_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if botao_id == "back-btn-pos" and etapa_atual > 0:
            return etapa_atual - 1, respostas

        if botao_id == "next-btn-pos":
            if etapa_atual > 0 and etapa_atual <= len(perguntas) and resposta_atual_lista and resposta_atual_lista[0] is not None:
                pergunta_id = perguntas[etapa_atual - 1]["id"]
                respostas[str(pergunta_id)] = resposta_atual_lista[0]
            return etapa_atual + 1, respostas

        raise PreventUpdate

    @app.callback(
        Output("mensagem-final-pos", "children"),
        Input("submit-btn-pos", "n_clicks"),
        State("respostas-pos", "data"),
        State("aluno-id", "data"),
        prevent_initial_call=True
    )
    def submeter(n_clicks, respostas, aluno_id):
        if not respostas:
            return "Por favor responde a todas as perguntas antes de submeter."

        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            for pergunta_id_str, answer_id in respostas.items():
                query = """
                    INSERT INTO forms_student_answers (student_id, question_id, answer_id)
                    VALUES (?, ?, ?)
                """
                params = (aluno_id, int(pergunta_id_str), int(answer_id))
                cursor.execute(query, params)
            conn.commit()
            conn.close()
            logger.info(f"[POS] Submissão concluída para aluno_id={aluno_id}")
            return "Obrigado! Respostas submetidas com sucesso."
        except Exception as e:
            logger.exception("[POS] Erro ao guardar respostas")
            return f"Erro ao guardar: {e}"

    @app.callback(
        Output("resultados-db-pos", "children"),
        Input("ver-resultados-btn-pos", "n_clicks"),
        prevent_initial_call=True
    )
    def ver_resultados(n):
        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            query = """
                SELECT q.question, r.answer, a.created_at
                FROM forms_student_answers a
                JOIN forms_questions q ON a.question_id = q.id
                JOIN forms_answers r ON a.answer_id = r.id
                WHERE q.form_type = 'pos'
                ORDER BY a.created_at DESC
                LIMIT 10
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            return html.Ul([
                html.Li(f"{ts} - {pergunta} → {resposta}") for pergunta, resposta, ts in rows
            ])
        except Exception as e:
            logger.exception("[POS] Erro ao carregar resultados")
            return f"Erro ao carregar resultados: {e}"