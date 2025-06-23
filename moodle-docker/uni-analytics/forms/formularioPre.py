import dash
from dash import html, dcc, Input, State, Output
from dash import ALL
from dash.exceptions import PreventUpdate
from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger

# Layout da página de formulário de Pré-Avaliação
def layout(user_id, item_id):
    logger.info(f"[PRE] Aluno com ID {user_id} acedeu ao formulário de pré-avaliação para o item {item_id}")
    return html.Div(className="formulario-wrapper", children=[
        html.Div(className="formulario-card", children=[
            dcc.Interval(id="init-load-pre", interval=1, n_intervals=0, max_intervals=1),
            html.H2("Pré-Avaliação", className="formulario-titulo"),

            # Armazenamento no navegador do estado do formulário
            dcc.Store(id='etapa-pre', data=0),              # Etapa atual (0 = introdução)
            dcc.Store(id='respostas-pre', data={}),         # Respostas dadas até ao momento
            dcc.Store(id='perguntas-pre'),                  # Perguntas carregadas da base de dados
            dcc.Store(id="aluno-id", data=user_id),         # Valor dinâmico vindo da sessão
            dcc.Store(id="item-id", data=item_id),          # Valor dinâmico vindo da sessão

            # Área onde se apresenta a pergunta atual
            html.Div(id='pergunta-area-pre', children="A carregar perguntas..."),

            html.Br(),

            # Botões de controlo
            html.Div([
                html.Button("Anterior", id="back-btn-pre", n_clicks=0, className="btn"),
                html.Button("Seguinte", id="next-btn-pre", n_clicks=0, className="btn"),
                html.Button("Submeter", id="submit-btn-pre", n_clicks=0, className="btn", style={"display": "none"}),
            ], style={
                "display": "flex",
                "gap": "20px",
                "justifyContent": "center", 
                "width": "100%"             
            }),

            # Mensagem após submissão
            html.Div(id="mensagem-final-pre", style={"marginTop": "20px", "fontWeight": "bold", "textAlign": "center"}),

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
        logger.debug(f"[PRE] Iniciar carregamento de perguntas com n_intervals={n}")
        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            query = """
                SELECT id, question
                FROM forms_questions
                WHERE form_type = 'pre'
                ORDER BY id ASC
            """
            logger.debug(f"[PRE] Executar query: {query.strip()}")
            cursor.execute(query)
            perguntas = cursor.fetchall()
            conn.close()
            logger.info(f"[PRE] Carregadas {len(perguntas)} perguntas.")
            return [{"id": p[0], "texto": p[1]} for p in perguntas]
        except Exception as e:
            logger.exception("[PRE] Erro ao carregar perguntas")
            return []

    # Mostra a introdução ou a pergunta atual e os botões adequados
    @app.callback(
        Output("pergunta-area-pre", "children"),
        Output("next-btn-pre", "style"),
        Output("submit-btn-pre", "style"),
        Output("back-btn-pre", "style"),
        Input("etapa-pre", "data"),
        Input("perguntas-pre", "data"),
        State("respostas-pre", "data")
    )

    def mostrar_pergunta(etapa, perguntas, respostas):
        if perguntas is None:
            raise PreventUpdate

        # Etapa de introdução
        if etapa == 0:
            return html.Div(
                "Bem-vindo ao formulário de pré-avaliação. As seguintes perguntas servem apenas para fins estatísticos e não serão associadas à tua identidade.",
                className="pergunta-card"
            ), {"display": "inline-block"}, {"display": "none"}, {"display": "none"}

        # Etapas de perguntas (1 até len(perguntas))
        if 1 <= etapa <= len(perguntas):
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
                logger.exception("[PRE] Erro ao carregar opções")
                opcoes = []

            return html.Div([
                html.Div(
                    f"Pergunta {etapa} de {len(perguntas)}",
                    className="barra-progresso-formulario"
                ),
                html.Label(pergunta_atual["texto"]),
                dcc.RadioItems(
                    id={"type": "resposta-pre", "index": etapa},
                    options=opcoes,
                    value=respostas.get(str(pergunta_id)) if str(pergunta_id) in respostas else (opcoes[0]["value"] if opcoes else None),
                    className="radio-dropdown",
                    labelStyle={"display": "block"}
                )
            ], className="pergunta-card"), {"display": "inline-block"}, {"display": "none"}, {"display": "inline-block" if etapa > 1 else "none"}


        # Etapa de confirmação antes da submissão
        if etapa == len(perguntas) + 1:
            return html.Div(
                "Confirmação: Estás prestes a submeter as tuas respostas.",
                className="pergunta-card"
            ), {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"}

        # Mensagem final depois de submeter
        return html.Div(
            "Obrigado! As tuas respostas vão ser submetidas.",
            className="mensagem-final-sucesso"
        ), {"display": "none"}, {"display": "none"}, {"display": "none"}

    # Callback unificado para avançar ou recuar entre perguntas
    @app.callback(
        Output("etapa-pre", "data"),                      # Atualiza a etapa atual
        Output("respostas-pre", "data"),                  # Atualiza as respostas dadas
        Input("next-btn-pre", "n_clicks"),                # Clicou em "Seguinte"
        Input("back-btn-pre", "n_clicks"),                # Clicou em "Anterior"
        State("etapa-pre", "data"),                       # Etapa atual
        State("respostas-pre", "data"),                   # Respostas dadas até agora
        State({"type": "resposta-pre", "index": ALL}, "value"),  # Valor da resposta atual
        State("perguntas-pre", "data"),                   # Lista de perguntas
        prevent_initial_call=True
    )
    def navegar(n_seguinte, n_anterior, etapa_atual, respostas, resposta_atual_lista, perguntas):
        ctx = dash.callback_context

        # Verifica se há evento ativo
        if not ctx.triggered or perguntas is None:
            raise PreventUpdate

        # Identifica qual botão foi clicado
        botao_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Se clicou no botão "Anterior"
        if botao_id == "back-btn-pre":
            if etapa_atual > 0:
                nova_etapa = etapa_atual - 1
                logger.debug(f"[PRE] Recuar para etapa {nova_etapa}")
                return nova_etapa, respostas
            else:
                raise PreventUpdate

        # Se clicou no botão "Seguinte"
        if botao_id == "next-btn-pre":
            if etapa_atual > 0 and etapa_atual <= len(perguntas) and resposta_atual_lista and resposta_atual_lista[0] is not None:
                pergunta_id = perguntas[etapa_atual - 1]["id"]
                respostas[str(pergunta_id)] = resposta_atual_lista[0]
                logger.debug(f"[PRE] Guardada resposta: pergunta_id={pergunta_id}, resposta_id={resposta_atual_lista[0]}")
            return etapa_atual + 1, respostas

        raise PreventUpdate

    # Submete todas as respostas para a base de dados
    @app.callback(
        Output("mensagem-final-pre", "children"),
        Input("submit-btn-pre", "n_clicks"),
        State("respostas-pre", "data"),
        State("aluno-id", "data"),
        State("item-id", "data"),
        prevent_initial_call=True
    )
    def submeter(n_clicks, respostas, aluno_id, item_id):
        if not respostas:
            return "Por favor responde a todas as perguntas antes de submeter."

        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()

            # Verificar se já existe submissão para este aluno e item_id
            cursor.execute(
                "SELECT 1 FROM forms_student_answers WHERE student_id = ? AND item_id = ? AND form_type = 'pre' LIMIT 1",
                (aluno_id, item_id)
            )
            if cursor.fetchone():
                conn.close()
                return "Só é possível fazer uma submissão de formulário para este E-fólio."

            # Inserir cada resposta
            for pergunta_id_str, answer_id in respostas.items():
                logger.debug(f"[PRE] A guardar resposta — Aluno {aluno_id}, Item {item_id}, Pergunta {pergunta_id_str}, Resposta {answer_id}")
                query = """
                    INSERT INTO forms_student_answers (student_id, item_id, question_id, answer_id, form_type)
                    VALUES (?, ?, ?, ?, ?)
                """
                params = (aluno_id, item_id, int(pergunta_id_str), int(answer_id), 'pre')
                logger.debug(f"[PRE] Executar INSERT: {query.strip()} | Params: {params}")
                cursor.execute(query, params)

            conn.commit()
            conn.close()
            logger.info(f"[PRE] Submissão concluída para aluno_id={aluno_id}, item_id={item_id}")
            return "Obrigado! Respostas submetidas com sucesso."

        except Exception as e:
            logger.exception("[PRE] Erro ao guardar respostas")
            return f"Erro ao guardar: {e}"