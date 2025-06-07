from dash import html, dcc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import queries.queriesAluno as qa
import queries.queriesGeral as qg
import traceback

# =========================
# Funções de lógica modular
# =========================

def calcular_pct_completions(dados, aluno_id, course_id, tipos, apenas_ids=None):
    # Filtra dados relevantes para o aluno e curso
    dados_filtrados = [
        d for d in dados
        if d['course_id'] == course_id
        and d['module_type'] in tipos
        and (apenas_ids is None or d['coursemodule_id'] in apenas_ids)
    ]

    # Conta apenas os módulos únicos disponíveis no curso
    ids_unicos = set(d['coursemodule_id'] for d in dados_filtrados)

    # Agora conta os completados pelo aluno
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
                if "aval" in grupo_aluno and any(e in nome for e in ["efolio", "global"]):
                    assigns_validos.append(d["coursemodule_id"])
                elif "exam" in grupo_aluno and "exame" in nome:
                    assigns_validos.append(d["coursemodule_id"])
    return assigns_validos

def calcular_desempenho_etl(dados, aluno_id, course_id):
    soma = 0.0
    for d in dados:
        if (
            d.get('course_id') == course_id and
            d.get('userid') == aluno_id and
            d.get('module_type') == 'assign' and
            d.get('finalgrade') is not None and
            any(e in (d.get("itemname") or "").lower() for e in ['efolio', 'global'])
        ):
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
        if d['userid'] == aluno_id
        and d['course_id'] == course_id
        and d['post_type'] == 'topic'
    )

def contar_respostas(dados, aluno_id, course_id):
    return sum(
        1 for d in dados
        if d['userid'] == aluno_id
        and d['course_id'] == course_id
        and d['post_type'] == 'reply'
    )

def contar_interacoes_aluno(dados, aluno_id, course_id):
    tipos = ['Ficheiros', 'Páginas', 'Links', 'Livros', 'Pastas', 'Quizzes']
    contagem = {tipo: 0 for tipo in tipos}
    for d in dados:
        if d['userid'] == aluno_id and d['courseid'] == course_id:
            tipo = d.get('tipo_interacao')
            if tipo in contagem:
                contagem[tipo] += 1
    return contagem

# =========================
# Layout principal
# =========================

def layout(aluno_id, course_id):
    try:
        dados_completions = qa.fetch_all_completions()
        dados_forum = qg.fetch_all_forum_posts()
        dados_interacoes = qa.fetch_all_interacoes()

        grupo_aluno = obter_grupo_aluno(dados_completions, aluno_id, course_id)
        assigns_validos = obter_assigns_validos(dados_completions, course_id, grupo_aluno)

        avaliacao = calcular_pct_completions(
            dados_completions, aluno_id, course_id, ['assign'], apenas_ids=assigns_validos
        )
        formativas = calcular_pct_completions(
            dados_completions, aluno_id, course_id, ['page', 'resource']
        )
        quizz = calcular_pct_completions(
            dados_completions, aluno_id, course_id, ['quiz']
        )
        progresso_global = calcular_pct_completions(
            dados_completions, aluno_id, course_id, ['assign', 'page', 'resource', 'quiz']
        )

        forum_criados = contar_topicos_criados(dados_forum, aluno_id, course_id)
        forum_respostas = contar_respostas(dados_forum, aluno_id, course_id)
        desempenho = calcular_desempenho_etl(dados_completions, aluno_id, course_id)

        interacoes = contar_interacoes_aluno(dados_interacoes, aluno_id, course_id)

    except Exception as e:
        print("[ERRO] (layout) Falha ao gerar o dashboard do aluno.")
        traceback.print_exc()
        return html.Div("Erro ao ligar à base de dados.")

    return html.Div(className="dashboard-grid", children=[
        html.Div(className="coluna-esquerda", children=[
            render_progresso_atividades(avaliacao, formativas, quizz),
            render_mensagens_forum(forum_criados, forum_respostas),
            render_volume_interacao(interacoes)
        ]),
        html.Div(className="coluna-direita", children=[
            render_progresso_global(progresso_global),
            render_desempenho(desempenho)
        ])
    ])

# =========================
# Componentes visuais
# =========================

def render_progresso_atividades(avaliacao, formativas, quizz):
    return html.Div(className="card card-progresso", children=[
        html.H4("Progresso das Actividades", className="card-section-title"),
        barra_personalizada("Avaliação", avaliacao, "#e2f396"),
        barra_personalizada("Formativas", formativas, "#76d19e"),
        barra_personalizada("Quizz", quizz, "#289c83"),
    ])

def render_mensagens_forum(criados, respondidos):
    return html.Div(className="card card-forum", children=[
        html.H4("Mensagens do fórum", className="card-section-title"),
        html.Div(className="forum-box", children=[
            html.Div(className="forum-created-box", children=[
                DashIconify(icon="mdi:email-outline", width=36, color="white"),
                html.Div("Criados", className="forum-label"),
                html.Div(str(criados), className="forum-number")
            ]),
            html.Div(className="forum-replied-box", children=[
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
        "Quizzes": "mdi:clipboard-outline"
    }

    cores = ["bg-yellow", "bg-green", "bg-darkgreen", "bg-blue", "bg-orange", "bg-teal"]

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
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=160)
    return html.Div(className="card card-gauge", children=[
        html.H4("Progresso", className="card-section-title"),
        html.Div(className="gauge-wrapper", children=[
            dcc.Graph(figure=fig, config={'displayModeBar': False})
        ])
    ])

def render_desempenho(nivel):
    if nivel == "Crítico":
        classe_cor = "indicador-critico"
    elif nivel == "Em Risco":
        classe_cor = "indicador-risco"
    else:
        classe_cor = "indicador-expectavel"
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
