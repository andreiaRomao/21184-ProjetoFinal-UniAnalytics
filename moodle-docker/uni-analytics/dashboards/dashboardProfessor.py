from dash import html
from dash_iconify import DashIconify
import queries.queriesProfessor as qp
import queries.queriesGeral as qg
import traceback
from datetime import datetime
from collections import defaultdict # para contagem de acessos semanais

from dashboards.dashboardGeral import layout as layout_geral

# =========================
# Funções de lógica modular
# =========================

def contar_conteudos_publicados(dados, professor_id, course_id):
    tipos = {
        'resource': 'Ficheiros',
        'page': 'Páginas',
        'url': 'Links',
        'book': 'Livros',
        'folder': 'Pastas',
        'quiz': 'Quizzes',
        'lesson': 'Lições' 
    }
    contagem = {nome: 0 for nome in tipos.values()}
    for d in dados:
        if d['course_id'] == course_id:
            tipo_raw = d.get('module_type')
            if tipo_raw in tipos:
                contagem[tipos[tipo_raw]] += 1
    return contagem

def contar_topicos_respostas_professor(dados, professor_id, course_id):
    criados = sum(1 for d in dados if d['userid'] == professor_id and d['course_id'] == course_id and d['post_type'] == 'topic')
    respondidos = sum(1 for d in dados if d['userid'] == professor_id and d['course_id'] == course_id and d['post_type'] == 'reply')
    return criados, respondidos

def calcular_velocidade_resposta(posts, professor_id, course_id):
    from datetime import datetime

    posts_curso = [p for p in posts if p["course_id"] == course_id]

    # Indexar posts por ID
    posts_por_id = {p["post_id"]: p for p in posts_curso}

    # Filtrar TODOS os posts feitos por aluno
    posts_aluno = [
        p for p in posts_curso 
        if "student" in (p.get("role") or "").lower()
    ]

    tempos_resposta = []

    for post_aluno in posts_aluno:
        post_id = post_aluno["post_id"]
        tempo_post = datetime.fromtimestamp(post_aluno["timecreated"])

        # Procurar respostas diretas feitas por professor
        respostas_professor = [
            p for p in posts_curso
            if p.get("parent") == post_id and "teacher" in (p.get("role") or "").lower()
        ]

        if respostas_professor:
            resposta = min(respostas_professor, key=lambda p: p["timecreated"])
            tempo_resposta = datetime.fromtimestamp(resposta["timecreated"])
            delta_horas = (tempo_resposta - tempo_post).total_seconds() / 3600
            tempos_resposta.append(delta_horas)

    if tempos_resposta:
        media = sum(tempos_resposta) / len(tempos_resposta)
        return round(media, 1)
    else:
        return None

def calcular_media_acessos_semanal(acessos, professor_id, course_id):
    # Filtra apenas acessos do professor ao curso
    acessos_prof = [
        a for a in acessos
        if a["userid"] == professor_id and a["courseid"] == course_id
    ]

    # Agrupa por ano+semana
    semanas = defaultdict(int)
    for acesso in acessos_prof:
        dt = acesso["access_time"]
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        ano_semana = dt.strftime("%Y-%W")
        semanas[ano_semana] += 1

    if semanas:
        media = sum(semanas.values()) / len(semanas)
        return round(media, 1)
    else:
        return 0

# =========================
# Layout principal
# =========================

def layout(professor_id, course_id):
    try:
        dados_conteudos = qp.fetch_conteudos_disponibilizados()
        contagem = contar_conteudos_publicados(dados_conteudos, professor_id, course_id)

        dados_forum = qg.fetch_all_forum_posts()
        topicos_criados, topicos_respondidos = contar_topicos_respostas_professor(dados_forum, professor_id, course_id)
        velocidade = calcular_velocidade_resposta(dados_forum, professor_id, course_id)

        dados_acessos = qp.fetch_course_access_logs()
        media_acessos = calcular_media_acessos_semanal(dados_acessos, professor_id, course_id)
        
    except Exception as e:
        print("[ERRO] (layout) Falha ao gerar o dashboard do professor.")
        traceback.print_exc()
        return html.Div("Erro ao ligar à base de dados.")

    return html.Div(children=[
        layout_geral(professor_id, course_id),  # Parte superior

        html.Div(
            children=[
                html.H3("Docente - Nível de Interação", className="dashboard-aluno-professor-titulo")
            ],
            style={"marginTop": "0px", "paddingTop": "0px", "marginBottom": "0px","paddingBottom": "0px"}
        ),

        html.Div(className="dashboard-professor", children=[
            html.Div(className="coluna-esquerda", children=[
                render_card_forum(topicos_criados, topicos_respondidos, velocidade, media_acessos)
            ]),
            html.Div(className="coluna-direita", children=[
                render_conteudos_publicados(contagem)
            ])
        ])
    ])


# =========================
# Componentes visuais
# =========================

def render_conteudos_publicados(contagem):
    icons = {
        "Ficheiros": "mdi:folder-outline",
        "Páginas": "mdi:file-document-outline",
        "Links": "mdi:link-variant",
        "Livros": "mdi:book-open-page-variant",
        "Pastas": "mdi:folder-outline",
        "Quizzes": "mdi:clipboard-outline",
        "Lições": "mdi:book-education-outline" 
    }
    cores = ["bg-yellow", "bg-green", "bg-darkgreen", "bg-blue", "bg-orange", "bg-teal","bg-purple"]

    return html.Div(className="card card-volume", children=[
        html.H4("Conteúdos Publicados", className="card-section-title"),
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

def render_card_forum(criados, respondidos, velocidade, media_acessos):
    return html.Div(className="card card-forum", children=[
        html.H4("Fórum - Tópicos", className="card-section-title"),
        html.Div(className="forum-box forum-grid", children=[
            html.Div(className="forum-created-box", children=[
                DashIconify(icon="mdi:email-outline", width=36, color="white"),
                html.Div("Criados", className="forum-label"),
                html.Div(str(criados), className="forum-number")
            ]),
            html.Div(className="forum-replied-box", children=[
                DashIconify(icon="mdi:email-send-outline", width=36, color="white"),
                html.Div("Respondidos", className="forum-label"),
                html.Div(str(respondidos), className="forum-number")
            ]),
            html.Div(className="forum-created-box", children=[
                DashIconify(icon="mdi:lock-outline", width=36, color="white"),
                html.Div("Média de acessos (semanal)", className="forum-label"),
                html.Div(f"{media_acessos}x/s", className="forum-number")
            ]),
            html.Div(className="forum-replied-box", children=[
                DashIconify(icon="mdi:clock-outline", width=36, color="white"),
                html.Div("Velocidade de Resposta", className="forum-label"),
                html.Div(f"{velocidade}h" if velocidade is not None else "—", className="forum-number")
            ])
        ])
    ])