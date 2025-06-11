from dash import html, dcc
from dash_iconify import DashIconify
import queries.queriesProfessor as qp
import queries.queriesGeral as qg
import queries.queriesAluno as qa
import plotly.graph_objects as go
import plotly.express as px
import traceback
import pandas as pd
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

def calcular_distribuicao_desempenho_global_professor(dados, course_id):
    distribuicao = {"Crítico": 0, "Em Risco": 0, "Expectável": 0}
    alunos = set(d["userid"] for d in dados if d["course_id"] == course_id and d.get("userid"))

    for aluno_id in alunos:
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
                    continue

        if soma < 3.5:
            distribuicao["Crítico"] += 1
        elif soma < 4.5:
            distribuicao["Em Risco"] += 1
        else:
            distribuicao["Expectável"] += 1

    return distribuicao


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

        dados_alunos = obter_dados_desempenho_alunos()

        dados_completions = qa.fetch_all_completions() 
        distribuicao = calcular_distribuicao_desempenho_global_professor(dados_completions, course_id)

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
            style={"marginTop": "0px", "paddingTop": "0px", "marginBottom": "0px", "paddingBottom": "0px"}
        ),

        html.Div(className="dashboard-professor", children=[
            html.Div(className="coluna-esquerda", children=[
                render_card_forum(topicos_criados, topicos_respondidos, velocidade, media_acessos)
            ]),
            html.Div(className="coluna-direita", children=[
                render_conteudos_publicados(contagem)
            ])
        ]),

        html.Div(
            children=[
                html.H3("Alunos - Desempenho", className="dashboard-aluno-professor-titulo")
            ],
            style={"marginTop": "0px", "paddingTop": "0px", "marginBottom": "0px", "paddingBottom": "0px"}
        ),

        # BLOCO 1: Conclusão com dois conjuntos (avaliativas + formativas)
        html.Div(className="linha-3-blocos", children=[
            render_card_conclusao_atividades(
                dados_alunos["gauge"],
                {
                    **dados_alunos["conclusao"]["avaliativas"],
                    **dados_alunos["conclusao"]["formativas"]
                }
            )
        ]),

        # BLOCO 2: Médias e Estado Global lado a lado
        render_card_mini_graficos(
            dados_alunos["medias"],
            distribuicao   
        )
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

# =========================

def render_card_medias_classificacao(dados):
    import plotly.graph_objects as go
    labels = list(dados.keys())
    valores = list(dados.values())
    cores = ["#f4f7b6", "#d4d4d4", "#195350", "#45b39c"]

    fig = go.Figure(go.Bar(
        x=valores,
        y=labels,
        orientation='h',
        marker=dict(color=cores),
        text=valores,
        textposition="auto"
    ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=200,
        yaxis=dict(autorange="reversed"),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    return html.Div(className="card-bloco", children=[
        html.H4("Média de classificações por atividade", className="card-section-title"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "160px"})
    ])

def render_card_conclusao_atividades(dados_gauge, dados_conclusao):
    def barra(label, valor):
        return html.Div(className="barra-container", children=[
            html.Div(label, className="barra-label"),
            html.Div(className="barra-fundo", children=[
                html.Div(className="barra-progresso", style={
                    "width": f"{valor}%",
                    "backgroundColor": "#9eff58"
                }),
                html.Div(f"{valor}%", className="barra-texto")
            ])
        ])

    def semicirculo(label, valor):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=valor,
            gauge={
                'shape': "angular",
                'axis': {'range': [0, 100]},
                'bar': {'color': "#9eff58"},
                'bgcolor': "#e6e6e6"
            },
            number={'font': {'size': 40}},
            title={"text": ""}
        ))
        fig.update_layout(
            margin=dict(t=20, b=0, l=0, r=0),
            height=100,
            width=130
        )
        
        return dcc.Graph(
            figure=fig,
            config={"displayModeBar": False},
            style={"height": "140px", "width": "130px", "margin": "0 auto"}
        )

    def bloco_conjunto(nome, valor_gauge, labels):
        return html.Div(className="bloco-conclusao-linha", children=[
            html.Div(className="bloco-conclusao-gauge", children=[
                semicirculo(nome, valor_gauge)
            ]),
            html.Div(className="bloco-conclusao-barras", children=[
                html.Div(nome, style={"fontWeight": "bold", "marginBottom": "6px"}),
                *[barra(label, dados_conclusao[label]) for label in labels]
            ])
        ])

    return html.Div(className="card-bloco card-bloco-conclusao", children=[
        html.H4("Taxa de Conclusão de Atividades", className="card-section-title"),
        bloco_conjunto("Avaliação", dados_gauge["avaliativas"], ["E-fólio A", "E-fólio B", "E-fólio Global"]),
        bloco_conjunto("Formativas", dados_gauge["formativas"], ["AF1", "AF2", "AF3"]),
        html.Div(style={"display": "flex", "justifyContent": "center", "marginTop": "0px"}, children=[
            html.Span("🟩 Concluídas", style={"marginRight": "12px"}),
            html.Span("⬜ Por concluir")
        ])
    ])



def render_card_mini_graficos(medias, distribuicao):
    return html.Div(className="bloco-mini-graficos", children=[
        render_card_medias_classificacao(medias),
        render_card_estado_global(distribuicao)
    ])


def render_card_estado_global(distribuicao):
    import plotly.graph_objects as go

    # Ordem garantida
    estados = ["Crítico", "Em Risco", "Expectável"]
    valores = [distribuicao.get(e, 0) for e in estados]
    cores = ["#dc3545", "#ffc107", "#28a745"]  # vermelho, amarelo, verde

    fig = go.Figure(data=[go.Pie(
        labels=estados,
        values=valores,
        hole=0.4,
        marker=dict(colors=cores),
        sort=False  # mantém a ordem
    )])

    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        height=200
    )

    return html.Div(className="card-bloco", children=[
        html.H4("Desempenho Global", className="card-section-title"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "160px"})
    ])


def obter_dados_desempenho_alunos():
    return {
        "medias": {
            "E-fólio A": 3.1,
            "E-fólio B": 2.5,
            "E-fólio Global": 8.6,
            "Total": 14.2
        },
        "conclusao": {
            "avaliativas": {
                "E-fólio A": 95,
                "E-fólio B": 62,
                "E-fólio Global": 32
            },
            "formativas": {
                "AF1": 53,
                "AF2": 78,
                "AF3": 89
            }
        },
        "gauge": {
            "avaliativas": 95,
            "formativas": 45
        },
        "estado_global": {
            "Crítico": 20,
            "Em Risco": 30,
            "Expectável": 50
        }
    }


