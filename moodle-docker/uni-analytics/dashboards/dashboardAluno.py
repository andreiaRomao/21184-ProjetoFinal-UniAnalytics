from dash import html, dcc, Input, Output, State
from dash_iconify import DashIconify
import plotly.graph_objects as go
import queries.queriesAluno as qa
import queries.queriesComuns as qg
import traceback
import re
from utils.logger import logger
import pandas as pd
import unicodedata

# =========================
# Funções de lógica modular
# =========================
def calcular_pct_completions(dados, user_id, course_id, tipos, grupo_aluno=None, apenas_ids=None):
    logger.debug("[PCT_COMPLETIONS] Início do cálculo de percentagem de completions")

    dados_filtrados = [
        d for d in dados
        if d['course_id'] == course_id
        and d['module_type'] in tipos
        and (apenas_ids is None or d['course_module_id'] in apenas_ids)
    ]

    if grupo_aluno:
        grupo_aluno = grupo_aluno.lower()
        dados_filtrados = [
            d for d in dados_filtrados
            if not (
                d['module_type'] == 'assign' and (
                    ("aval" in grupo_aluno and "exame" in normalizar_itemname(d.get('item_name') or "")) or
                    ("exam" in grupo_aluno and any(e in normalizar_itemname(d.get('item_name') or "") for e in ['efolio', 'global']))
                )
            )
        ]

    ids_unicos = set(d['course_module_id'] for d in dados_filtrados)
    completados = set(
        d['course_module_id']
        for d in dados_filtrados
        if d.get('user_id') == user_id and d.get('completion_state') == 1
    )

    total = len(ids_unicos)
    concluidos = len(completados)

    logger.debug(f"[PCT_COMPLETIONS] Total: {total}, Concluídos: {concluidos}")
    return round(concluidos / total * 100) if total > 0 else 0

def obter_grupo_aluno(dados, user_id, course_id):
    for d in dados:
        if d['user_id'] == user_id and d['course_id'] == course_id and d.get("group_name"):
            return d["group_name"].lower()
    return None

def obter_assigns_validos(dados, course_id, grupo_aluno):
    assigns_validos = []
    for d in dados:
        if d["course_id"] == course_id and d["module_type"] == "assign":
            nome = normalizar_itemname(d.get("item_name") or "")
            grupo = (d.get("group_name") or "").lower()

            if grupo_aluno and grupo_aluno in grupo:
                if "aval" in grupo_aluno and "efolio" in nome and "global" not in nome:
                    assigns_validos.append(d["course_module_id"])
                elif "exam" in grupo_aluno and "exame" in nome:
                    assigns_validos.append(d["course_module_id"])
    logger.debug(f"[ASSIGNS_VALIDOS] Total: {len(assigns_validos)}")
    return assigns_validos

def calcular_desempenho_etl(dados, user_id, course_id):
    grupo_aluno = None
    for d in dados:
        if d.get("user_id") == user_id and d.get("course_id") == course_id:
            grupo_aluno = (d.get("group_name") or "").strip().lower()
            break

    if not grupo_aluno or "aval" not in grupo_aluno:
        return "Não Aplicável"

    soma = 0.0
    for d in dados:
        if (
            d.get("course_id") == course_id and
            d.get("user_id") == user_id and
            d.get("module_type") == "assign" and
            d.get("final_grade") is not None
        ):
            nome = normalizar_itemname(d.get("item_name") or "")
            if any(e in nome for e in ['efolio', 'global']):
                try:
                    soma += float(d['final_grade'])
                except (ValueError, TypeError):
                    logger.warning(f"[DESEMPENHO] Nota inválida ignorada: {d['final_grade']}")
                    continue

    logger.debug(f"[DESEMPENHO] Soma final: {soma}")
    if soma < 3.5:
        return "Crítico"
    elif soma < 4.5:
        return "Em Risco"
    else:
        return "Expectável"

def contar_topicos_criados(dados, user_id, course_id):
    total = sum(
        1 for d in dados
        if d['user_id'] == user_id
        and d['course_id'] == course_id
        and d['post_type'] == 'topic'
    )
    logger.debug(f"[TOPICOS] Criados: {total}")
    return total

def contar_respostas(dados, user_id, course_id):
    total = sum(
        1 for d in dados
        if d['user_id'] == user_id
        and d['course_id'] == course_id
        and d['post_type'] == 'reply'
    )
    logger.debug(f"[RESPOSTAS] Total: {total}")
    return total

def contar_interacoes_aluno(dados, user_id, course_id):
    tipos = [
        'Ficheiros', 'Páginas', 'Links', 'Livros', 'Pastas',
        'Quizzes', 'Lições', 'Conteúdos Multimédia'
    ]
    contagem = {tipo: 0 for tipo in tipos}

    for d in dados:
        if d['user_id'] == user_id and d['course_id'] == course_id:
            tipo = d.get('tipo_interacao')
            if tipo in contagem:
                contagem[tipo] += 1

    logger.debug(f"[INTERAÇÕES] Contagem: {contagem}")
    return contagem

def get_dashboard_top_info(user_id, course_id):
    try:
        cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())

        linha = cursos[(cursos['user_id'] == user_id) & (cursos['course_id'] == course_id)].head(1)

        if not linha.empty:
            nome = linha['name'].values[0]
            papel_raw = linha['role'].values[0].lower()
            papel = "ALUNO" if "student" in papel_raw else "PROFESSOR"
            nome_curso = linha['course_name'].values[0]
        else:
            nome = "Utilizador Desconhecido"
            papel = "-"
            nome_curso = f"{course_id} - UC Desconhecida"

        return nome, papel, nome_curso

    except Exception as e:
        logger.exception(f"[ERRO] (get_dashboard_top_info): {e}")
        return "Erro", "Erro", "Erro"

def extrair_ano_letivo(course_name):
    match = re.search(r'_(\d{2})', course_name)
    if match:
        sufixo = int(match.group(1))
        ano_inicio = 2000 + sufixo
        return f"{ano_inicio}/{ano_inicio + 1}"
    return None

def obter_progresso_avaliacao(dados_completions, user_id, course_id, grupo_aluno, assigns_validos):
    mostrar = not grupo_aluno or "exam" not in grupo_aluno
    if mostrar:
        valor = calcular_pct_completions(
            dados_completions, user_id, course_id, ['assign'], apenas_ids=assigns_validos
        )
    else:
        valor = 0
    logger.debug(f"[PROGRESSO_AVALIACAO] Mostrar: {mostrar}, Valor: {valor}%")
    return mostrar, valor

def obter_opcoes_dropdown_cursos(user_id):
    try:
        cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())
        cursos_user = cursos[cursos['user_id'] == user_id].copy()

        # Extrair o ano letivo de cada course_name
        cursos_user['ano_letivo'] = cursos_user['course_name'].apply(extrair_ano_letivo)

        # Determinar o ano letivo mais recente (atual)
        anos_validos = sorted(cursos_user['ano_letivo'].dropna().unique())
        if not anos_validos:
            return []
        ano_atual = anos_validos[-1]

        # Filtrar apenas as do ano atual
        cursos_filtrados = cursos_user[cursos_user['ano_letivo'] == ano_atual].copy()

        # Extrai uc_id para evitar duplicados
        cursos_filtrados['uc_id'] = cursos_filtrados['course_name'].str.extract(r'(\d{5})')

        # Ordenar e eliminar duplicados por uc_id
        cursos_ordenados = cursos_filtrados.sort_values(by="course_name", ascending=False)
        cursos_unicos = cursos_ordenados.drop_duplicates(subset=["uc_id"])

        opcoes = [
            {"label": linha['course_name'], "value": linha['course_id']}
            for _, linha in cursos_unicos.iterrows()
        ]

        logger.debug(f"[Dropdown] Ano letivo atual: {ano_atual}, opções: {opcoes}")
        return opcoes

    except Exception as e:
        logger.error("[ERRO] (obter_opcoes_dropdown_cursos):", exc_info=True)
        return []

def normalizar_itemname(nome):
    if not isinstance(nome, str):
        logger.warning(f"[NORMALIZAR] Nome inválido (não string): {nome}")
        return ""
    
    nome_original = nome
    # Remove acentuação
    nome = unicodedata.normalize("NFKD", nome).encode("ASCII", "ignore").decode("utf-8")
    nome = nome.lower()
    nome = re.sub(r'[^a-z0-9]', '', nome)
    
    logger.debug(f"[NORMALIZAR] '{nome_original}' normalizado para '{nome}'")
    return nome

def register_callbacks(app):
    @app.callback(
        Output("info_nome_utilizador_aluno", "children"),
        Output("info_nome_curso_aluno", "children"),
        Input("dropdown_uc_aluno", "value"),
        State("store_user_id_aluno", "data")
    )
    def atualizar_topo_info_aluno(novo_course_id, user_id):
        nome, papel, nome_curso = get_dashboard_top_info(user_id, novo_course_id)
        return f"[{papel}] {nome}", nome_curso

    @app.callback(
        Output("conteudo_dashboard_aluno", "children"),
        Input("dropdown_uc_aluno", "value"),
        State("store_user_id_aluno", "data")
    )
    def atualizar_dashboard_aluno(course_id, user_id):
        return gerar_dashboard_conteudo(user_id, course_id)

# =========================
# Layout principal
# =========================

def layout(user_id):
    try:
        cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())
        cursos_user = cursos[cursos['user_id'] == user_id].copy()

        cursos_user['ano_letivo'] = cursos_user['course_name'].apply(extrair_ano_letivo)
        anos_validos = sorted(cursos_user['ano_letivo'].dropna().unique())
        ano_atual = anos_validos[-1] if anos_validos else None

        cursos_user['uc_id'] = cursos_user['course_name'].str.extract(r'(\d{5})')
        cursos_ordenados = cursos_user.sort_values(by="course_name", ascending=False)
        cursos_unicos = cursos_ordenados.drop_duplicates(subset=["uc_id"])
        cursos_ano_atual = cursos_unicos[cursos_unicos['ano_letivo'] == ano_atual]

        course_id_inicial = cursos_ano_atual['course_id'].values[0] if not cursos_ano_atual.empty else None

        return html.Div(children=[
            dcc.Store(id="store_user_id_aluno", data=user_id),
            html.Div(id="conteudo_dashboard_aluno", children=gerar_dashboard_conteudo(user_id, course_id_inicial))
        ])

    except Exception as e:
        logger.exception("[ERRO] (layout - dashboardAluno):")
        return html.Div("Erro ao carregar o dashboard do aluno.")
    
def gerar_dashboard_conteudo(user_id, course_id):
    try:
        dados_completions = qg.fetch_all_grade_progress_local()
        dados_forum = qg.fetch_all_forum_posts_local()
        dados_interacoes = qa.fetch_all_interacoes_local()

        grupo_aluno = obter_grupo_aluno(dados_completions, user_id, course_id)
        assigns_validos = obter_assigns_validos(dados_completions, course_id, grupo_aluno)

        mostrar_avaliacao, avaliacao = obter_progresso_avaliacao(
            dados_completions, user_id, course_id, grupo_aluno, assigns_validos
        )

        progresso_global = calcular_pct_completions(
            dados_completions, user_id, course_id, ['page', 'resource', 'quiz', 'lesson'], grupo_aluno=grupo_aluno
        )

        forum_criados = contar_topicos_criados(dados_forum, user_id, course_id)
        forum_respostas = contar_respostas(dados_forum, user_id, course_id)
        desempenho = calcular_desempenho_etl(dados_completions, user_id, course_id)
        interacoes = contar_interacoes_aluno(dados_interacoes, user_id, course_id)

    except Exception as e:
        print("[ERRO] (gerar_dashboard_conteudo) Falha ao gerar dados.")
        traceback.print_exc()
        return html.Div("Erro ao carregar dados.")

    coluna_esquerda = []
    if mostrar_avaliacao:
        coluna_esquerda.append(render_progresso_atividades(avaliacao))
    coluna_esquerda.append(render_desempenho(desempenho))

    return html.Div(children=[
        html.Div(className="topo-dashboard", children=[
            html.Div(className="linha-superior", children=[
                html.Div(className="info-utilizador", children=[
                    DashIconify(
                        icon="mdi:school",
                        width=32,
                        color="#2c3e50",
                        className="avatar-icon"
                    ),
                    html.Span(id="info_nome_utilizador_aluno", className="nome-utilizador")
                ]),
                html.Div(className="dropdown-curso", children=[
                    dcc.Dropdown(
                        id="dropdown_uc_aluno",
                        options=obter_opcoes_dropdown_cursos(user_id),
                        value=course_id,
                        clearable=False,
                        className="dropdown-uc-selector"
                    )
                ])
            ]),
            html.Div(className="barra-uc", children=[
                html.Span(id="info_nome_curso_aluno", className="nome-curso"),
                html.Span(extrair_ano_letivo(get_dashboard_top_info(user_id, course_id)[2]) or "", className="ano-letivo")
            ])
        ]),

        html.Div(children=[
            html.H2("Informação Geral do Aluno", style={
                "fontSize": "26px",
                "fontWeight": "bold",
                "color": "#2c3e50",
                "marginBottom": "8px",
                "text-align": "center"
            })
        ]),
        html.Div(className="dashboard-aluno-titulos-blocos", children=[
            html.Div(className="titulo-bloco-esquerdo", children=[
                html.H3("Evolução da Avaliação")
            ]),
            html.Div(className="titulo-bloco-direito", children=[
                html.H3("Nível de Interação")
            ])
        ]),

        html.Div(className="dashboard-aluno-3colunas", children=[
            html.Div(className="dashboard-aluno-coluna", children=coluna_esquerda),
            html.Div(className="dashboard-aluno-coluna", children=[
                render_volume_interacao(interacoes)
            ]),
            html.Div(className="dashboard-aluno-coluna", children=[
                render_mensagens_forum(forum_criados, forum_respostas),
                render_progresso_global(progresso_global)
            ])
        ])
    ])

# =========================
# Componentes visuais
# =========================

def render_progresso_atividades(avaliacao):
    return html.Div(className="card card-progresso", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Progresso da Avaliação", className="tooltip-hover card-section-title"),
            html.Span(
                "Contabiliza automaticamente os e-fólios realizados pelo aluno nesta unidade curricular.",
                className="tooltip-text"
            )
        ]),
        barra_personalizada("Avaliação", avaliacao, "#e2f396")
    ])

def render_mensagens_forum(criados, respondidos):
    return html.Div(className="card card-forum", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Mensagens do Fórum", className="tooltip-hover card-section-title"),
            html.Span(
                "Mensagens publicadas pelo aluno nos fóruns da UC.\n"
                "• Criados: tópicos novos iniciados pelo aluno\n"
                "• Respondidos: respostas dadas a outros colegas ou ao professor",
                className="tooltip-text"
            )
        ]),
        html.Div(className="dashboard-aluno-forum-box", children=[
            html.Div(className="dashboard-aluno-forum-item", children=[
                DashIconify(icon="mdi:email-outline", width=36, color="white"),
                html.Div("Criados", className="forum-label"),
                html.Div(str(criados), className="forum-number")
            ]),
            html.Div(className="dashboard-aluno-forum-item dashboard-aluno-forum-item-respondido", children=[
                DashIconify(icon="mdi:email-send-outline", width=36, color="white"),
                html.Div("Respondidos", className="forum-label"),
                html.Div(str(respondidos), className="forum-number")
            ])
        ])
    ])

def render_volume_interacao(contagem):
    icons = {
        "Ficheiros": "mdi:folder-outline",
        "Páginas": "mdi:file-document-outline",
        "Links": "mdi:link-variant",
        "Livros": "mdi:book-open-page-variant",
        "Pastas": "mdi:folder-outline",
        "Quizzes": "mdi:clipboard-outline",
        "Lições": "mdi:book-education-outline",
        "Conteúdos Multimédia": "mdi:video-box"  
    }

    cores = ["bg-yellow", "bg-green", "bg-darkgreen", "bg-blue", "bg-orange", "bg-teal", "bg-purple", "bg-pink"]

    return html.Div(className="card card-volume", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Volume de Interação", className="tooltip-hover card-section-title"),
            html.Span(
                "Contagem de interações do aluno com os conteúdos da UC, como ficheiros, quizzes e páginas.\n"
                "Os dados são extraídos dos registos de logs de atividade.",
                className="tooltip-text"
            )
        ]),
        html.Ul(className="volume-list", children=[
            html.Li(className="volume-item", children=[
                html.Div(className=f"volume-icon-bg {cores[i]}", children=[
                    DashIconify(icon=icons[tipo], width=24, color="white")
                ]),
                html.Span(tipo),
                html.Span(str(contagem.get(tipo, 0)), className="volume-number")
            ]) for i, tipo in enumerate(icons)
        ])
    ])

def render_progresso_global(progresso_pct):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=progresso_pct,
        number={
            'suffix': '%',
            'font': {'size': 24, 'color': "#2c3e50", 'family': 'sans-serif'}
        },
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': '#7cc3ac', 'thickness': 0.3},
            'bgcolor': "#f9f9f9",
            'borderwidth': 0,
            'steps': [{'range': [0, 100], 'color': "#dfeeee"}]
        }
    ))
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=120)

    return html.Div(className="card card-gauge", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Progresso das Atividades", className="tooltip-hover card-section-title"),
            html.Span(
                "Percentagem de conteúdos pedagógicos concluídos: como páginas, ficheiros, quizzes e lições interativas da UC.",
                className="tooltip-text"
            )
        ]),
        html.Div(className="gauge-wrapper", children=[
            dcc.Graph(figure=fig, config={'displayModeBar': False})
        ])
    ])

def render_desempenho(nivel):
    if nivel == "Crítico":
        classe_cor = "indicador-critico"
    elif nivel == "Em Risco":
        classe_cor = "indicador-risco"
    elif nivel == "Expectável":
        classe_cor = "indicador-expectavel"
    else:
        classe_cor = "indicador-neutro"  # Para "Não Aplicável"

    return html.Div(className="card card-desempenho", children=[
        html.Div(className="tooltip-bloco", children=[
            html.Div("Desempenho", className="tooltip-hover card-section-title"),
            html.Span(
                "Indica o desempenho atual do aluno com base nas notas dos e-fólios realizados.\n"
                "Categorizado de acordo com a soma das notas em:\n"
                "- Expectável: ≥ 4.5 valores \n"
                "- Em Risco: entre 3.5 e 4.5 valores \n"
                "- Crítico: abaixo de 3.5 valores \n"
                "- Não Aplicável: Aluno fora do regime de Avaliação Contínua",
                className="tooltip-text"
            )
        ]),
        html.Div(nivel, className=f"desempenho-indicador {classe_cor}", style={"marginTop": "12px"})
    ])

def barra_personalizada(label, valor, cor_primaria):
    return html.Div(className="barra-container", children=[
        html.Div(label, className="barra-label", style={"marginTop": "12px"}),
        html.Div(className="barra-fundo", children=[
            html.Div(style={"width": f"{valor}%", "backgroundColor": cor_primaria}, className="barra-progresso"),
            html.Div(f"{valor}%", className="barra-texto")
        ])
    ])    

def render_topo_geral(user_id, course_id):
    nome, papel, curso = get_dashboard_top_info(user_id, course_id)
    ano_curso_atual = extrair_ano_letivo(curso) or ""
    return html.Div(className="topo-dashboard", children=[
        html.Div(className="linha-superior", children=[
            html.Div(className="info-utilizador", children=[
                DashIconify(
                    icon="mdi:school" if papel == "ALUNO" else "mdi:teach",
                    width=32,
                    color="#2c3e50",
                    className="avatar-icon"
                ),
                html.Span(f"[{papel}] {nome}", className="nome-utilizador")
            ])
        ]),
        html.Div(className="barra-uc", children=[
            html.Span(curso, className="nome-curso"),
            html.Span(ano_curso_atual, className="ano-letivo")
        ])
    ])

__all__ = ["layout", "register_callbacks"]