import dash
from dash import html, dcc, Input, State, Output
from dash import ALL
from dash.exceptions import PreventUpdate
from db.formsDatabase import connect_to_forms_db


# Layout da página de formulário de Pré-Avaliação
def layout():
    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            dcc.Interval(id="init-load-pre", interval=1, n_intervals=0, max_intervals=1),
            html.H2("Pré-Avaliação", className="card-title"),

            # Armazenamento no navegador do estado do formulário
            dcc.Store(id='etapa-pre', data=0),              # Etapa atual (0 = introdução)
            dcc.Store(id='respostas-pre', data={}),         # Respostas dadas até ao momento
            dcc.Store(id='perguntas-pre'),                  # Perguntas carregadas da base de dados
            dcc.Store(id="aluno-id", data=999),             #Placeholder para ID do aluno (para ser dinâmico mais tarde)

            # Área onde se apresenta a pergunta atual
            html.Div(id='pergunta-area-pre', children="A carregar perguntas..."),

            html.Br(),

            # Botões de controlo
            html.Div([
                html.Button("Seguinte", id="next-btn-pre", n_clicks=0, className="btn"),
                html.Button("Submeter", id="submit-btn-pre", n_clicks=0, className="btn", style={"display": "none"}),
                html.Button("Ver Resultados", id="ver-resultados-btn-pre", n_clicks=0, className="btn")
            ], style={"display": "flex", "gap": "20px"}),

            # Mensagem após submissão
            html.Div(id="mensagem-final-pre", style={"marginTop": "20px", "fontWeight": "bold", "textAlign": "center"}),

            # Resultados recentes da BD
            html.Div(id="resultados-db-pre", style={"marginTop": "20px"})
        ])
    ])

# Função que regista todos os callbacks necessários
def register_callbacks(app):

    # Carrega as perguntas do tipo 'pre' ao entrar na página
    @app.callback(
        Output("perguntas-pre", "data"),
        Input("init-load-pre", "n_intervals")
    )
    def carregar_perguntas(n):
        print("[carregar_perguntas] Callback iniciado com n_intervals =", n)

        try:
            print("[carregar_perguntas] A estabelecer ligação à base de dados...")
            conn = connect_to_forms_db()
            cursor = conn.cursor()

            print("[carregar_perguntas] A executar query às perguntas...")
            cursor.execute("""
                SELECT id, pergunta
                FROM formularios_perguntas
                WHERE tipo_formulario = 'pre'
                ORDER BY id ASC
            """)
            perguntas = cursor.fetchall()

            print(f"[carregar_perguntas] Total de perguntas obtidas: {len(perguntas)}")
            for p in perguntas:
                print(f"  Pergunta ID={p[0]} → {p[1]}")

            conn.close()
            print("[carregar_perguntas] Ligação à base de dados fechada.")

            return [{"id": p[0], "texto": p[1]} for p in perguntas]

        except Exception as e:
            print("[carregar_perguntas] Erro ao aceder à base de dados:", e)
            return []

    # Mostra a introdução ou a pergunta atual e os botões adequados
    @app.callback(
        Output("pergunta-area-pre", "children"),
        Output("next-btn-pre", "style"),
        Output("submit-btn-pre", "style"),
        Input("etapa-pre", "data"),
        Input("perguntas-pre", "data"),
        State("respostas-pre", "data")
    )
    def mostrar_pergunta(etapa, perguntas, respostas):
        if perguntas is None:
            raise PreventUpdate

        # Etapa 0: introdução
        if etapa == 0:
            return html.Div(
                "Bem-vindo ao formulário de pré-avaliação. As seguintes perguntas servem apenas para fins estatísticos e não serão associadas à tua identidade."
            ), {"display": "inline-block"}, {"display": "none"}

        # Etapa além do número de perguntas → mostrar botão de submissão
        if etapa > len(perguntas):
            return html.Div("Obrigado! As tuas respostas vão ser submetidas."), {"display": "none"}, {"display": "inline-block"}

        # Carrega pergunta e opções
        pergunta_atual = perguntas[etapa - 1]
        pergunta_id = pergunta_atual["id"]

        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("SELECT resposta FROM formularios_respostas WHERE pergunta_id = ?", (pergunta_id,))
            rows = cursor.fetchall()
            conn.close()
            opcoes = [r[0] for r in rows]
        except Exception as e:
            print("Erro ao carregar opções:", e)
            opcoes = []

        return html.Div([
            html.Label(pergunta_atual["texto"]),
            dcc.Dropdown(
                id={"type": "resposta-pre", "index": etapa}, 
                options=[{"label": o, "value": o} for o in opcoes],
                placeholder="Seleciona uma opção",
                value=respostas.get(str(pergunta_id))
            )
        ]), {"display": "inline-block"}, {"display": "none"}

    # Guarda a resposta atual e passa para a próxima pergunt
    @app.callback(
        Output("etapa-pre", "data"),
        Output("respostas-pre", "data"),
        Input("next-btn-pre", "n_clicks"),
        State("etapa-pre", "data"),
        State("respostas-pre", "data"),
        State({"type": "resposta-pre", "index": ALL}, "value"),  # ← MATCH com dicionário dinâmico
        State("perguntas-pre", "data"),
        prevent_initial_call=True
    )
    def avancar(n_clicks, etapa, respostas, resposta_atual_lista, perguntas):
        if perguntas is None:
            raise dash.exceptions.PreventUpdate

        # Só guarda se tiver havido dropdown válido
        if etapa > 0 and etapa <= len(perguntas) and resposta_atual_lista and resposta_atual_lista[0] is not None:
            pergunta_id = perguntas[etapa - 1]["id"]
            respostas[str(pergunta_id)] = resposta_atual_lista[0]

        return etapa + 1, respostas

    # Submete todas as respostas para a base de dados
    @app.callback(
        Output("mensagem-final-pre", "children"),
        Input("submit-btn-pre", "n_clicks"),
        State("respostas-pre", "data"),
        State("aluno-id", "data"),
        prevent_initial_call=True
    )
    def submeter(n_clicks, respostas, aluno_id):
        if not respostas:
            return "Por favor responde a todas as perguntas antes de submeter."

        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            for pergunta_id_str, resposta in respostas.items():
                cursor.execute(
                    "INSERT INTO alunos_respostas (pergunta_id, resposta, aluno_id) VALUES (?, ?, ?)",
                    (int(pergunta_id_str), resposta, aluno_id)
                )
            conn.commit()
            conn.close()
            return "Obrigado! Respostas submetidas com sucesso."
        except Exception as e:
            print("Erro ao guardar respostas:", e)
            return f"Erro ao guardar: {e}"

    # Mostra os últimos 10 registos na base de dados
    @app.callback(
        Output("resultados-db-pre", "children"),
        Input("ver-resultados-btn-pre", "n_clicks"),
        prevent_initial_call=True
    )
    def ver_resultados(n):
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.pergunta, a.resposta, a.created_at
                FROM alunos_respostas a
                JOIN formularios_perguntas p ON a.pergunta_id = p.id
                WHERE p.tipo_formulario = 'pre'
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