from dash import html
from dash_iconify import DashIconify
import queries.queriesProfessor as qp
import queries.queriesGeral as qg
import traceback

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
        'quiz': 'Quizzes'
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

# =========================
# Layout principal
# =========================

def layout(professor_id, course_id):
    try:
        dados_conteudos = qp.fetch_conteudos_disponibilizados()
        contagem = contar_conteudos_publicados(dados_conteudos, professor_id, course_id)

        dados_forum = qg.fetch_all_forum_posts()
        topicos_criados, topicos_respondidos = contar_topicos_respostas_professor(dados_forum, professor_id, course_id)
    except Exception as e:
        print("[ERRO] (layout) Falha ao gerar o dashboard do professor.")
        traceback.print_exc()
        return html.Div("Erro ao ligar à base de dados.")

    return html.Div(children=[
        layout_geral(professor_id, course_id),  # Parte superior
    
        html.Div(
            children=[
                html.H3("Professor - Visão Geral da Atividade", style={
                    "textAlign": "center",
                    "marginTop": "4px",
                    "marginBottom": "8px"
                })
            ],
            style={"marginTop": "0px", "paddingTop": "0px"}
        ),
    
        html.Div(className="dashboard-professor", children=[
            html.Div(className="coluna-esquerda", children=[
                render_card_forum(topicos_criados, topicos_respondidos)
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
        "Quizzes": "mdi:clipboard-outline"
    }
    cores = ["bg-yellow", "bg-green", "bg-darkgreen", "bg-blue", "bg-orange", "bg-teal"]

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

def render_card_forum(criados, respondidos):
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
                html.Div("5x/s", className="forum-number")
            ]),
            html.Div(className="forum-replied-box", children=[
                DashIconify(icon="mdi:clock-outline", width=36, color="white"),
                html.Div("Velocidade de Resposta", className="forum-label"),
                html.Div("42h", className="forum-number")
            ])
        ])
    ])