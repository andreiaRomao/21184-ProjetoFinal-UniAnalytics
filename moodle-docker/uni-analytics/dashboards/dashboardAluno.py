from dash import html, dcc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import queries.queriesAluno as qa
import queries.queriesComuns as qg
import traceback
import re


# =========================
# Funções de lógica modular
# =========================

def calcular_pct_completions(dados, aluno_id, course_id, tipos, grupo_aluno=None, apenas_ids=None):
    # Filtra dados relevantes para o aluno e curso
    dados_filtrados = [
        d for d in dados
        if d['course_id'] == course_id
        and d['module_type'] in tipos
        and (apenas_ids is None or d['coursemodule_id'] in apenas_ids)
    ]

    # Excluir atividades irrelevantes conforme o grupo
    if grupo_aluno:
        grupo_aluno = grupo_aluno.lower()
        dados_filtrados = [
            d for d in dados_filtrados
            if not (
                d['module_type'] == 'assign' and (
                    # Excluir "exame" e "exame de recurso" para Avaliação Contínua
                    ("aval" in grupo_aluno and any(e in (d.get('itemname') or '').lower() for e in ['exame'])) or
                    # Excluir "efolios" e "global" para grupo Exame
                    ("exam" in grupo_aluno and any(e in (d.get('itemname') or '').lower() for e in ['efolio', 'global']))
                )
            )
        ]

    # IDs únicos e completados
    ids_unicos = set(d['coursemodule_id'] for d in dados_filtrados)
    completados = set(
        d['coursemodule_id']
        for d in dados_filtrados
        if d.get('userid') == aluno_id and d.get('completionstate') == 1
    )

    total = len(ids_unicos)
    concluidos = len(completados)

    return round(concluidos / total * 100) if total > 0 else 0

def obter_grupo_aluno(dados, aluno_id, course_id):
    for d in dados:
        if d['userid'] == aluno_id and d['course_id'] == course_id and d.get("groupname"):
            return d["groupname"].lower()
    return None

def obter_assigns_validos(dados, course_id, grupo_aluno):
    assigns_validos = []
    for d in dados:
        if d["course_id"] == course_id and d["module_type"] == "assign":
            nome = (d.get("itemname") or "").lower()
            grupo = (d.get("groupname") or "").lower()

            if grupo_aluno and grupo_aluno in grupo:
                if "aval" in grupo_aluno and "efolio" in nome and "global" not in nome:
                    assigns_validos.append(d["coursemodule_id"])
                elif "exam" in grupo_aluno and "exame" in nome:
                    assigns_validos.append(d["coursemodule_id"])
    return assigns_validos

def calcular_desempenho_etl(dados, aluno_id, course_id):
    grupo_aluno = None
    for d in dados:
        if d.get("userid") == aluno_id and d.get("course_id") == course_id:
            grupo_aluno = (d.get("groupname") or "").strip().lower()
            break

    # Se não tiver grupo ou não for grupo "aval", retorna "Não Aplicável"
    if not grupo_aluno or "aval" not in grupo_aluno:
        return "Não Aplicável"

    soma = 0.0
    for d in dados:
        if (
            d.get("course_id") == course_id and
            d.get("userid") == aluno_id and
            d.get("module_type") == "assign" and
            d.get("finalgrade") is not None
        ):
            nome = (d.get("itemname") or "").lower()
            if any(e in nome for e in ['efolio', 'global']):
                try:
                    soma += float(d['finalgrade'])
                except (ValueError, TypeError):
                    print(f"[AVISO] Nota inválida ignorada: {d['finalgrade']}")
                    continue

    if soma < 3.5:
        return "Crítico"
    elif soma < 4.5:
        return "Em Risco"
    else:
        return "Expectável"


def contar_topicos_criados(dados, aluno_id, course_id):
    return sum(
        1 for d in dados
        if d['user_id'] == aluno_id
        and d['course_id'] == course_id
        and d['post_type'] == 'topic'
    )

def contar_respostas(dados, aluno_id, course_id):
    return sum(
        1 for d in dados
        if d['user_id'] == aluno_id
        and d['course_id'] == course_id
        and d['post_type'] == 'reply'
    )

def contar_interacoes_aluno(dados, aluno_id, course_id):
    tipos = [
        'Ficheiros', 'Páginas', 'Links', 'Livros', 'Pastas',
        'Quizzes', 'Lições', 'Conteúdos Multimédia'
    ]
    contagem = {tipo: 0 for tipo in tipos}

    for d in dados:
        if d['user_id'] == aluno_id and d['course_id'] == course_id:
            tipo = d.get('tipo_interacao')

            if tipo in contagem:
                contagem[tipo] += 1

    return contagem

def get_dashboard_top_info(userid, course_id):
    try:
        cursos = qg.fetch_user_course_data()

        # Filtra apenas pelo utilizador e curso atual
        linha = cursos[(cursos['userid'] == userid) & (cursos['courseid'] == course_id)].head(1)

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
        print("[ERRO] (get_dashboard_top_info):", e)
        return "Erro", "Erro", "Erro"

def extrair_ano_letivo(course_name):    
    match = re.search(r'_(\d{2})', course_name)
    if match:
        sufixo = int(match.group(1))
        ano_inicio = 2000 + sufixo
        return f"{ano_inicio}/{ano_inicio + 1}"
    return None

def obter_progresso_avaliacao(dados_completions, aluno_id, course_id, grupo_aluno, assigns_validos):
    mostrar = not grupo_aluno or "exam" not in grupo_aluno
    if mostrar:
        valor = calcular_pct_completions(
            dados_completions, aluno_id, course_id, ['assign'], apenas_ids=assigns_validos
        )
    else:
        valor = 0
    return mostrar, valor

# =========================
# Layout principal
# =========================

def layout(aluno_id, course_id):
    try:
        dados_completions = qg.fetch_all_completions()
        dados_forum = qg.fetch_all_forum_posts_local()
        dados_interacoes = qa.fetch_all_interacoes_local()

        grupo_aluno = obter_grupo_aluno(dados_completions, aluno_id, course_id)
        assigns_validos = obter_assigns_validos(dados_completions, course_id, grupo_aluno)

        # Se for grupo de exame, não mostrar progresso de avaliação
        mostrar_avaliacao, avaliacao = obter_progresso_avaliacao(
            dados_completions, aluno_id, course_id, grupo_aluno, assigns_validos
        )

        progresso_global = calcular_pct_completions(
            dados_completions, aluno_id, course_id, ['page', 'resource', 'quiz', 'lesson'], grupo_aluno=grupo_aluno
        )

        forum_criados = contar_topicos_criados(dados_forum, aluno_id, course_id)
        forum_respostas = contar_respostas(dados_forum, aluno_id, course_id)
        desempenho = calcular_desempenho_etl(dados_completions, aluno_id, course_id)

        interacoes = contar_interacoes_aluno(dados_interacoes, aluno_id, course_id)

    except Exception as e:
        print("[ERRO] (layout) Falha ao gerar o dashboard do aluno.")
        traceback.print_exc()
        return html.Div("Erro ao ligar à base de dados.")

    # Bloco da coluna da esquerda (progresso avaliação + desempenho)
    coluna_esquerda = []
    if mostrar_avaliacao:
        coluna_esquerda.append(render_progresso_atividades(avaliacao))
    coluna_esquerda.append(render_desempenho(desempenho))

    return html.Div(children=[
        render_topo_geral(aluno_id, course_id),

        html.Div(children=[
            html.H2("Informação Geral do aluno", style={
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
        html.H4("Progresso da Avaliação", className="card-section-title"),
        barra_personalizada("Avaliação", avaliacao, "#e2f396")
    ])

def render_mensagens_forum(criados, respondidos):
    return html.Div(className="card card-forum", children=[
        html.H4("Mensagens do fórum", className="card-section-title"),
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
        html.H4("Volume de Interação", className="card-section-title"),
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
        html.H4("Progresso das Atividades", className="card-section-title"),
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
        classe_cor = "indicador-neutro"  # ← Para "Não Aplicável"
    
    return html.Div(className="card card-desempenho", children=[
        html.H4("Desempenho", className="card-section-title"),
        html.Div(nivel, className=f"desempenho-indicador {classe_cor}")
    ])


def barra_personalizada(label, valor, cor_primaria):
    return html.Div(className="barra-container", children=[
        html.Div(label, className="barra-label"),
        html.Div(className="barra-fundo", children=[
            html.Div(style={"width": f"{valor}%", "backgroundColor": cor_primaria}, className="barra-progresso"),
            html.Div(f"{valor}%", className="barra-texto")
        ])
    ])    

def render_topo_geral(userid, course_id):
    nome, papel, curso = get_dashboard_top_info(userid, course_id)
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