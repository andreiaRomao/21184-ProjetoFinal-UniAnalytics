import dash
from dash import html, dcc, Input, State, Output
from dash import ALL
from dash.exceptions import PreventUpdate
from db.uniAnalytics import connect_to_forms_db


# Layout da página do formulário de Pós-Avaliação
def layout():
    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            dcc.Interval(id="init-load-pos", interval=1, n_intervals=0, max_intervals=1),
            html.H2("Pós-Avaliação", className="card-title"),

            # Armazenamento de estado no navegador
            dcc.Store(id='etapa-pos', data=0),            # Etapa atual do formulário
            dcc.Store(id='respostas-pos', data={}),       # Respostas do utilizador
            dcc.Store(id='perguntas-pos'),                # Perguntas carregadas da base de dados
            dcc.Store(id="aluno-id", data=999),           # ID do aluno (placeholder por agora)

            # Área onde será apresentada a pergunta atual
            html.Div(id='pergunta-area-pos', children="A carregar perguntas..."),

            html.Br(),

            # Botões de navegação
            html.Div([
                html.Button("Seguinte", id="next-btn-pos", n_clicks=0, className="btn"),
                html.Button("Submeter", id="submit-btn-pos", n_clicks=0, className="btn", style={"display": "none"}),
                html.Button("Ver Resultados", id="ver-resultados-btn-pos", n_clicks=0, className="btn")
            ], style={"display": "flex", "gap": "20px"}),

            # Mensagem final
            html.Div(id="mensagem-final-pos", style={"marginTop": "20px", "fontWeight": "bold", "textAlign": "center"}),

            # Resultados recentes gravados na BD
            html.Div(id="resultados-db-pos", style={"marginTop": "20px"})
        ])
    ])

# Callbacks para o formulário de Pós-Avaliação
def register_callbacks(app):

    # Carrega as perguntas do tipo 'pos' ao iniciar
    @app.callback(
        Output("perguntas-pos", "data"),
        Input("init-load-pos", "n_intervals")
    )
    def carregar_perguntas(n):
        print("[carregar_perguntas POS] Callback iniciado com n_intervals =", n)
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, question
                FROM forms_questions
                WHERE form_type = 'pos'
                ORDER BY id ASC
            """)
            perguntas = cursor.fetchall()
            conn.close()
            return [{"id": p[0], "texto": p[1]} for p in perguntas]
        except Exception as e:
            print("[carregar_perguntas POS] Erro:", e)
            return []

    # Mostra a introdução ou a pergunta atual
    @app.callback(
        Output("pergunta-area-pos", "children"),
        Output("next-btn-pos", "style"),
        Output("submit-btn-pos", "style"),
        Input("etapa-pos", "data"),
        Input("perguntas-pos", "data"),
        State("respostas-pos", "data")
    )
    def mostrar_pergunta(etapa, perguntas, respostas):
        if perguntas is None:
            raise PreventUpdate

        if etapa == 0:
            return html.Div(
                "Bem-vindo ao formulário de pós-avaliação. As seguintes perguntas servem apenas para fins estatísticos e não serão associadas à tua identidade."
            ), {"display": "inline-block"}, {"display": "none"}

        if etapa > len(perguntas):
            return html.Div("Obrigado! As tuas respostas vão ser submetidas."), {"display": "none"}, {"display": "inline-block"}

        pergunta_atual = perguntas[etapa - 1]
        pergunta_id = pergunta_atual["id"]

        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, answer FROM forms_answers WHERE question_id = ?", (pergunta_id,))
            rows = cursor.fetchall()
            conn.close()
            opcoes = [{"label": r[1], "value": r[0]} for r in rows]  # value = id
        except Exception as e:
            print("[mostrar_pergunta POS] Erro ao carregar opções:", e)
            opcoes = []

        return html.Div([
            html.Label(pergunta_atual["texto"]),
            dcc.Dropdown(
                id={"type": "resposta-pos", "index": etapa},
                options=opcoes,
                placeholder="Seleciona uma opção",
                value=respostas.get(str(pergunta_id))  # resposta guardada é o ID
            )
        ]), {"display": "inline-block"}, {"display": "none"}

    # Guarda a resposta atual e passa para a próxima pergunta
    @app.callback(
        Output("etapa-pos", "data"),
        Output("respostas-pos", "data"),
        Input("next-btn-pos", "n_clicks"),
        State("etapa-pos", "data"),
        State("respostas-pos", "data"),
        State({"type": "resposta-pos", "index": ALL}, "value"),
        State("perguntas-pos", "data"),
        prevent_initial_call=True
    )
    def avancar(n_clicks, etapa, respostas, resposta_atual_lista, perguntas):
        if perguntas is None:
            raise PreventUpdate

        if etapa > 0 and etapa <= len(perguntas) and resposta_atual_lista and resposta_atual_lista[0] is not None:
            pergunta_id = perguntas[etapa - 1]["id"]
            respostas[str(pergunta_id)] = resposta_atual_lista[0]  # guarda o ID da resposta

        return etapa + 1, respostas

    # Submete todas as respostas para a base de dados
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
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            for pergunta_id_str, answer_id in respostas.items():
                cursor.execute(
                    "INSERT INTO forms_student_answers (student_id, question_id, answer_id) VALUES (?, ?, ?)",
                    (aluno_id, int(pergunta_id_str), int(answer_id))
                )
            conn.commit()
            conn.close()
            return "Obrigado! Respostas submetidas com sucesso."
        except Exception as e:
            print("Erro ao guardar respostas POS:", e)
            return f"Erro ao guardar: {e}"

    # Mostra os últimos 10 registos na base de dados
    @app.callback(
        Output("resultados-db-pos", "children"),
        Input("ver-resultados-btn-pos", "n_clicks"),
        prevent_initial_call=True
    )
    def ver_resultados(n):
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.question, r.answer, a.created_at
                FROM forms_student_answers a
                JOIN forms_questions q ON a.question_id = q.id
                JOIN forms_answers r ON a.answer_id = r.id
                WHERE q.form_type = 'pos'
                ORDER BY a.created_at DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            conn.close()
            return html.Ul([
                html.Li(f"{ts} - {pergunta} → {resposta}") for pergunta, resposta, ts in rows
            ])
        except Exception as e:
            return f"Erro ao carregar resultados: {e}"
