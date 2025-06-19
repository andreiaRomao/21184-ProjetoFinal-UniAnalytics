from dash import html, dcc, Input, Output, State, ctx
import dash
import datetime
from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger

# Layout principal da página de administração de perguntas
def layout():
    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            html.H2("Administração de Perguntas dos Formulários", className="card-title"),

            # Dropdown para escolher o tipo de formulário
            html.Div(className="form-group", children=[
                html.Label("Tipo de Formulário"),
                dcc.Dropdown(
                    id="tipo-formulario-admin",
                    options=[
                        {"label": "Pré-Avaliação", "value": "pre"},
                        {"label": "Pós-Avaliação", "value": "pos"}
                    ],
                    placeholder="Escolhe o tipo de formulário",
                    className="pergunta-opcao"
                ),
            ]),

            # Campo para inserir o texto da nova pergunta
            html.Div(className="form-group", children=[
                html.Label("Texto da Pergunta"),
                dcc.Input(
                    id="nova-pergunta",
                    type="text",
                    placeholder="Escreve a pergunta",
                    style={"width": "100%"},
                    className="pergunta-opcao"
                )
            ]),

            # Campo para inserir as opções de resposta (uma por linha)
            html.Div(className="form-group", children=[
                html.Label("Opções de Resposta (uma por linha)"),
                dcc.Textarea(
                    id="opcoes-resposta",
                    placeholder="Ex: Sim\nNão\nTalvez",
                    style={"width": "100%", "height": 100},
                    className="pergunta-opcao"
                )
            ]),

            # Botões de ação: guardar, listar e apagar perguntas
            html.Div(style={
                        "marginTop": "20px",
                        "display": "flex",
                        "gap": "10px",
                        "flexWrap": "wrap",
                        "justifyContent": "center", 
                        "width": "100%" 
                    }, children=[
                html.Button("Guardar Pergunta", id="guardar-pergunta-btn", className="btn"),
                html.Button("Listar Perguntas", id="listar-perguntas-btn", className="btn"),
                html.Button("Apagar Pergunta", id="mostrar-apagar-btn", className="btn"),
                html.Button("Editar Pergunta", id="mostrar-editar-btn", className="btn")
            ]),

            # Zona que será preenchida com inputs e botões para apagar pergunta
            html.Div(id="apagar-section", children=[], style={"marginTop": "20px"}),

            # Zona que será preenchida com inputs e botões para editar pergunta
            html.Div(id="editar-section", children=[], style={"marginTop": "20px"}),

            # Zona para apresentar mensagens ao utilizador
            html.Div(id="mensagem-admin", style={"marginTop": "20px", "fontWeight": "bold"}),

            html.Hr(),

            # Secção oculta inicialmente para listar perguntas
            html.Div(id="secao-lista-perguntas", style={"display": "none"}, children=[
                html.H4("Perguntas Registadas", className="card-section-title"),
                html.Div(id="lista-perguntas", className="pergunta-card")
            ])
        ])
    ])

# Callback principal da página
def register_callbacks(app):

    # Callback para guardar nova pergunta e respetivas opções
    @app.callback(
        Output("mensagem-admin", "children"),
        Output("lista-perguntas", "children"),
        Input("guardar-pergunta-btn", "n_clicks"),
        State("tipo-formulario-admin", "value"),
        State("nova-pergunta", "value"),
        State("opcoes-resposta", "value"),
        prevent_initial_call=True
    )
    def guardar_pergunta(n, tipo, pergunta, opcoes_raw):
        # Validação dos campos obrigatórios
        if not tipo or not pergunta or not opcoes_raw:
            return "Por favor preenche todos os campos.", dash.no_update

        # Processa e valida o número de opções
        opcoes = [o.strip() for o in opcoes_raw.split("\n") if o.strip()]
        if len(opcoes) < 2:
            return "A pergunta deve ter pelo menos duas opções de resposta.", dash.no_update
        if len(opcoes) > 6:
            return "A pergunta não pode ter mais de seis opções de resposta.", dash.no_update

        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            now = datetime.datetime.now().isoformat()

            # Inserção da nova pergunta
            query_q = """
                INSERT INTO forms_questions (question, form_type, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """
            logger.debug(f"[ADMIN] INSERT pergunta: {query_q.strip()} | Params: {pergunta}, {tipo}")
            cursor.execute(query_q, (pergunta, tipo, now, now))
            pergunta_id = cursor.lastrowid

            # Inserção das opções de resposta associadas
            for opcao in opcoes:
                query_a = """
                    INSERT INTO forms_answers (question_id, answer, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """
                logger.debug(f"[ADMIN] INSERT resposta: {opcao} para question_id={pergunta_id}")
                cursor.execute(query_a, (pergunta_id, opcao, now, now))

            conn.commit()
            conn.close()
            logger.info(f"[ADMIN] Pergunta inserida com sucesso: id={pergunta_id}")
            return "Pergunta guardada com sucesso!", listar_perguntas_html(tipo)

        except Exception as e:
            logger.exception("[ADMIN] Erro ao guardar pergunta")
            return f"Erro ao guardar: {str(e)}", dash.no_update

    # Gera a lista de perguntas formatada
    def listar_perguntas_html(tipo_form=None):
        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()

            # Query dependendo se há filtro de tipo de formulário
            if tipo_form:
                query = """
                    SELECT q.id, q.question, q.form_type, q.created_at, q.updated_at, a.answer
                    FROM forms_questions q
                    LEFT JOIN forms_answers a ON q.id = a.question_id
                    WHERE q.form_type = ?
                    ORDER BY q.created_at DESC
                """
                cursor.execute(query, (tipo_form,))
            else:
                query = """
                    SELECT q.id, q.question, q.form_type, q.created_at, q.updated_at, a.answer
                    FROM forms_questions q
                    LEFT JOIN forms_answers a ON q.id = a.question_id
                    ORDER BY q.created_at DESC
                """
                cursor.execute(query)

            rows = cursor.fetchall()
            conn.close()

            # Reorganiza as respostas por pergunta
            perguntas_dict = {}
            for pid, pergunta, tipo, created_at, updated_at, resposta in rows:
                if pid not in perguntas_dict:
                    perguntas_dict[pid] = {
                        "pergunta": pergunta,
                        "tipo": tipo,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "respostas": []
                    }
                if resposta:
                    perguntas_dict[pid]["respostas"].append(resposta)

            # Cria o layout visual da lista de perguntas
            return html.Ul([
                html.Li([
                    html.B(f"ID {pid} — [{dados['tipo'].upper()}] {dados['pergunta']}"),
                    html.Div(f"Criada em: {dados['created_at']} | Atualizada em: {dados['updated_at']}", style={"fontSize": "0.9em", "color": "gray"}),
                    html.Ul([html.Li(r) for r in dados['respostas']])
                ]) for pid, dados in perguntas_dict.items()
            ])

        except Exception as e:
            logger.exception("[ADMIN] Erro ao listar perguntas")
            return f"Erro ao carregar perguntas: {str(e)}"

    # Mostra as perguntas após clique no botão "Listar Perguntas"
    @app.callback(
        Output("lista-perguntas", "children", allow_duplicate=True),
        Output("secao-lista-perguntas", "style", allow_duplicate=True),
        Input("listar-perguntas-btn", "n_clicks"),
        State("tipo-formulario-admin", "value"),
        prevent_initial_call=True
    )
    def mostrar_perguntas(n_clicks, tipo_form):
        return listar_perguntas_html(tipo_form), {"display": "block"}

    # Mostra input para introduzir o ID da pergunta a apagar
    @app.callback(
        Output("apagar-section", "children"),
        Input("mostrar-apagar-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def mostrar_input_apagar(n):
        return html.Div(className="form-group", style={"marginTop": "20px"}, children=[
            html.Label("ID da Pergunta a Apagar"),
            dcc.Input(
                id="id-pergunta-apagar",
                type="number",
                placeholder="Insere o ID da pergunta",
                style={"width": "200px"},
                className="pergunta-opcao"
            ),
            html.Button(
                "Confirmar Apagar",
                id="apagar-pergunta-btn",
                className="btn",
                style={"marginLeft": "10px", "backgroundColor": "#dc3545"}
            )
        ])

    # Apaga pergunta e respetivas respostas associadas
    @app.callback(
        Output("mensagem-admin", "children", allow_duplicate=True),  # Mensagem de confirmação ou erro
        Output("lista-perguntas", "children", allow_duplicate=True),  # Atualiza lista de perguntas após remoção
        Output("secao-lista-perguntas", "style", allow_duplicate=True),  # Garante que a secção está visível
        Input("apagar-pergunta-btn", "n_clicks"),
        State("id-pergunta-apagar", "value"),
        State("tipo-formulario-admin", "value"),
        prevent_initial_call=True
    )
    def apagar_pergunta(n_clicks, pergunta_id, tipo_form):
        # Valida se foi introduzido um ID
        if not pergunta_id:
            return "Por favor insere um ID válido para apagar.", dash.no_update, dash.no_update

        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()

            # Verifica se a pergunta com o ID fornecido existe
            cursor.execute("SELECT COUNT(*) FROM forms_questions WHERE id = ?", (pergunta_id,))
            existe = cursor.fetchone()[0]
            if existe == 0:
                conn.close()
                return f"A pergunta com ID {pergunta_id} não existe.", dash.no_update, dash.no_update

            # Apaga as respostas associadas à pergunta
            cursor.execute("DELETE FROM forms_answers WHERE question_id = ?", (pergunta_id,))

            # Apaga a pergunta propriamente dita
            cursor.execute("DELETE FROM forms_questions WHERE id = ?", (pergunta_id,))

            conn.commit()
            conn.close()

            logger.info(f"[ADMIN] Pergunta apagada com sucesso: id={pergunta_id}")
            return f"Pergunta ID {pergunta_id} apagada com sucesso.", listar_perguntas_html(tipo_form), {"display": "block"}

        except Exception as e:
            logger.exception("[ADMIN] Erro ao apagar pergunta")
            return f"Erro ao apagar: {str(e)}", dash.no_update, dash.no_update

        if not pergunta_id:
            return "Por favor insere um ID válido para apagar.", dash.no_update, dash.no_update

        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM forms_answers WHERE question_id = ?", (pergunta_id,))
            cursor.execute("DELETE FROM forms_questions WHERE id = ?", (pergunta_id,))
            conn.commit()
            conn.close()
            logger.info(f"[ADMIN] Pergunta apagada com sucesso: id={pergunta_id}")
            return f"Pergunta ID {pergunta_id} apagada com sucesso.", listar_perguntas_html(tipo_form), {"display": "block"}
        except Exception as e:
            logger.exception("[ADMIN] Erro ao apagar pergunta")
            return f"Erro ao apagar: {str(e)}", dash.no_update, dash.no_update

    # Mostra os inputs para editar pergunta (ID, novo texto e respostas)
    @app.callback(
        Output("editar-section", "children"),
        Input("mostrar-editar-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def mostrar_input_editar(n):
        return html.Div([
            dcc.Store(id="dados-pergunta-store"),
            html.Div(className="form-group", children=[
                html.Label("ID da Pergunta a Editar"),
                dcc.Input(
                    id="id-pergunta-editar",
                    type="number",
                    placeholder="Insere o ID da pergunta",
                    className="pergunta-opcao"
                ),
                html.Button(
                    "Carregar Dados",
                    id="carregar-pergunta-btn",
                    className="btn",
                    style={"marginTop": "10px"}
                )
            ]),
            html.Div(id="editar-formulario-preenchido")
        ])
    
    # Callback para editar uma pergunta existente
    @app.callback(
        Output("mensagem-admin", "children", allow_duplicate=True),
        Output("lista-perguntas", "children", allow_duplicate=True),
        Output("secao-lista-perguntas", "style", allow_duplicate=True),
        Input("editar-pergunta-btn", "n_clicks"),
        State("id-pergunta-editar", "value"),
        State("novo-texto-pergunta", "value"),
        State("novas-respostas", "value"),
        State("tipo-formulario-admin", "value"),
        State("dados-pergunta-store", "data"),
        prevent_initial_call=True
    )
    def editar_pergunta(n_clicks, pergunta_id, novo_texto, novas_respostas_raw, tipo_form, dados_store):
        if not pergunta_id:
            return "Por favor preenche o ID da pergunta.", dash.no_update, dash.no_update

        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()
            now = datetime.datetime.now().isoformat()

            # Atualizar texto da pergunta se fornecido
            if novo_texto:
                cursor.execute(
                    "UPDATE forms_questions SET question = ?, updated_at = ? WHERE id = ?",
                    (novo_texto, now, pergunta_id)
                )

            # Atualizar respostas se fornecido
            if novas_respostas_raw:
                novas_respostas = [r.strip() for r in novas_respostas_raw.split("\n") if r.strip()]
                if len(novas_respostas) != dados_store.get("num_respostas", 0):
                    return "O número de respostas não pode ser alterado.", dash.no_update, dash.no_update

                cursor.execute("SELECT id FROM forms_answers WHERE question_id = ?", (pergunta_id,))
                respostas_ids = [r[0] for r in cursor.fetchall()]

                for rid, novo_texto_r in zip(respostas_ids, novas_respostas):
                    cursor.execute(
                        "UPDATE forms_answers SET answer = ?, updated_at = ? WHERE id = ?",
                        (novo_texto_r, now, rid)
                    )

            conn.commit()
            conn.close()

            logger.info(f"[ADMIN] Pergunta ID {pergunta_id} editada com sucesso.")
            return f"Pergunta ID {pergunta_id} editada com sucesso.", listar_perguntas_html(tipo_form), {"display": "block"}

        except Exception as e:
            logger.exception("[ADMIN] Erro ao editar")
            return f"Erro ao editar: {str(e)}", dash.no_update, dash.no_update

    @app.callback(
        Output("editar-formulario-preenchido", "children"),
        Output("dados-pergunta-store", "data"),
        Input("carregar-pergunta-btn", "n_clicks"),
        State("id-pergunta-editar", "value"),
        prevent_initial_call=True
    )
    def carregar_dados_pergunta(n_clicks, pergunta_id):
        if not pergunta_id:
            return "Por favor insere um ID válido.", dash.no_update

        try:
            conn = connect_to_uni_analytics_db()
            cursor = conn.cursor()

            cursor.execute("SELECT question FROM forms_questions WHERE id = ?", (pergunta_id,))
            row = cursor.fetchone()
            if not row:
                return f"Pergunta com ID {pergunta_id} não encontrada.", dash.no_update

            texto_pergunta = row[0]

            cursor.execute("SELECT answer FROM forms_answers WHERE question_id = ?", (pergunta_id,))
            respostas = [r[0] for r in cursor.fetchall()]

            conn.close()

            return html.Div(className="form-group", children=[
                html.Label("Texto da Pergunta"),
                dcc.Input(
                    id="novo-texto-pergunta",
                    type="text",
                    value=texto_pergunta,
                    className="pergunta-opcao"
                ),
                html.Label("Editar Respostas (uma por linha)"),
                dcc.Textarea(
                    id="novas-respostas",
                    value="\n".join(respostas),
                    className="pergunta-opcao",
                    style={"width": "100%", "height": "100px"}
                ),
                html.Button(
                    "Atualizar Pergunta",
                    id="editar-pergunta-btn",
                    className="btn",
                    style={"marginTop": "10px"}
                )
            ]), {
                "num_respostas": len(respostas)
            }

        except Exception as e:
            logger.exception("[ADMIN] Erro ao carregar dados da pergunta")
            return f"Erro ao carregar dados: {str(e)}", dash.no_update