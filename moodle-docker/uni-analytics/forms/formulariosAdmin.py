from dash import html, dcc, Input, Output, State, ctx
import dash
import datetime
from db.formsDatabase import connect_to_forms_db

# Layout principal da página de administração de perguntas
def layout():
    return html.Div(className="dashboard-container", children=[
        html.Div(className="card", children=[
            html.H2("Administração de Perguntas dos Formulários", className="card-title"),

            # Seletor do tipo de formulário
            html.Label("Tipo de Formulário"),
            dcc.Dropdown(
                id="tipo-formulario-admin",
                options=[
                    {"label": "Pré-Avaliação", "value": "pre"},
                    {"label": "Pós-Avaliação", "value": "pos"}
                ],
                placeholder="Escolhe o tipo de formulário"
            ),

            html.Br(),
            # Campo de texto para nova pergunta
            html.Label("Texto da Pergunta"),
            dcc.Input(id="nova-pergunta", type="text", placeholder="Escreve a pergunta", style={"width": "100%"}),

            html.Br(), html.Br(),
            # Campo de texto para opções de resposta
            html.Label("Opções de Resposta (uma por linha)"),
            dcc.Textarea(id="opcoes-resposta", placeholder="Ex: Sim\nNão\nTalvez", style={"width": "100%", "height": 100}),

            html.Br(),
            html.Button("Guardar Pergunta", id="guardar-pergunta-btn", className="btn"),

            html.Br(), html.Br(),
            html.Button("Listar Perguntas", id="listar-perguntas-btn", className="btn"),

            html.Br(), html.Br(),
            html.Button("Apagar Pergunta", id="mostrar-apagar-btn", className="btn"),

            # Div para mostrar o campo de input do ID quando o botão for clicado
            html.Div(id="apagar-section", children=[], style={"marginTop": "10px"}),

            html.Div(id="mensagem-admin", style={"marginTop": "20px", "fontWeight": "bold"}),

            html.Hr(),
            html.H4("Perguntas Registadas"),
            html.Div(id="lista-perguntas")
        ])
    ])

# Registo dos callbacks da interface
def register_callbacks(app):

    # Guardar nova pergunta com respetivas opções
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
        if not tipo or not pergunta or not opcoes_raw:
            return "Por favor preenche todos os campos.", dash.no_update

        opcoes = [o.strip() for o in opcoes_raw.split("\n") if o.strip()]
        if not opcoes:
            return "Adiciona pelo menos uma opção de resposta.", dash.no_update

        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            now = datetime.datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO formularios_perguntas (pergunta, tipo_formulario, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (pergunta, tipo, now, now))
            pergunta_id = cursor.lastrowid

            for opcao in opcoes:
                cursor.execute("""
                    INSERT INTO formularios_respostas (pergunta_id, resposta, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (pergunta_id, opcao, now, now))

            conn.commit()
            conn.close()
            return "Pergunta guardada com sucesso!", listar_perguntas_html(tipo)
        except Exception as e:
            return f"Erro ao guardar: {str(e)}", dash.no_update

    # Função auxiliar para listar perguntas (com ou sem filtro por tipo)
    def listar_perguntas_html(tipo_form=None):
        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()

            if tipo_form:
                cursor.execute("""
                    SELECT p.id, p.pergunta, p.tipo_formulario, p.created_at, p.updated_at, r.resposta
                    FROM formularios_perguntas p
                    LEFT JOIN formularios_respostas r ON p.id = r.pergunta_id
                    WHERE p.tipo_formulario = ?
                    ORDER BY p.created_at DESC
                """, (tipo_form,))
            else:
                cursor.execute("""
                    SELECT p.id, p.pergunta, p.tipo_formulario, p.created_at, p.updated_at, r.resposta
                    FROM formularios_perguntas p
                    LEFT JOIN formularios_respostas r ON p.id = r.pergunta_id
                    ORDER BY p.created_at DESC
                """)
            rows = cursor.fetchall()
            conn.close()

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

            return html.Ul([
                html.Li([
                    html.B(f"ID {pid} — [{dados['tipo'].upper()}] {dados['pergunta']}"),
                    html.Div(f"Criada em: {dados['created_at']} | Atualizada em: {dados['updated_at']}", style={"fontSize": "0.9em", "color": "gray"}),
                    html.Ul([html.Li(r) for r in dados['respostas']])
                ]) for pid, dados in perguntas_dict.items()
            ])
        except Exception as e:
            return f"Erro ao carregar perguntas: {str(e)}"

    # Listar perguntas (ao clicar no botão)
    @app.callback(
        Output("lista-perguntas", "children", allow_duplicate=True),
        Input("listar-perguntas-btn", "n_clicks"),
        State("tipo-formulario-admin", "value"),
        prevent_initial_call=True
    )
    def mostrar_perguntas(n_clicks, tipo_form):
        return listar_perguntas_html(tipo_form)

    # Atualizar lista automaticamente ao mudar o tipo de formulário
    @app.callback(
        Output("lista-perguntas", "children", allow_duplicate=True),
        Input("tipo-formulario-admin", "value"),
        prevent_initial_call=True
    )
    def atualizar_lista_por_tipo(tipo):
        return listar_perguntas_html(tipo)

    # Mostrar campo para apagar pergunta ao clicar no botão
    @app.callback(
        Output("apagar-section", "children"),
        Input("mostrar-apagar-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def mostrar_input_apagar(n):
        return html.Div([
            dcc.Input(id="id-pergunta-apagar", type="number", placeholder="Insere o ID da pergunta", style={"width": "50%"}),
            html.Button("Confirmar Apagar", id="apagar-pergunta-btn", className="btn", style={"marginLeft": "10px", "color": "red"})
        ])

    # Callback para apagar pergunta após introdução do ID
    @app.callback(
        Output("mensagem-admin", "children", allow_duplicate=True),
        Output("lista-perguntas", "children", allow_duplicate=True),
        Input("apagar-pergunta-btn", "n_clicks"),
        State("id-pergunta-apagar", "value"),
        State("tipo-formulario-admin", "value"),
        prevent_initial_call=True
    )
    def apagar_pergunta(n_clicks, pergunta_id, tipo_form):
        if not pergunta_id:
            return "Por favor insere um ID válido para apagar.", dash.no_update

        try:
            conn = connect_to_forms_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM formularios_respostas WHERE pergunta_id = ?", (pergunta_id,))
            cursor.execute("DELETE FROM formularios_perguntas WHERE id = ?", (pergunta_id,))
            conn.commit()
            conn.close()
            return f"Pergunta ID {pergunta_id} apagada com sucesso.", listar_perguntas_html(tipo_form)
        except Exception as e:
            return f"Erro ao apagar: {str(e)}", dash.no_update