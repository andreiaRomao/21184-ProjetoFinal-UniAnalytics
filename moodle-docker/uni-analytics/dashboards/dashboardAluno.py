from dash import html, dcc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import queries.queriesAluno as qa

def layout(aluno_id, course_id):
    try:
        avaliacao = qa.fetch_user_course_avaliation(aluno_id, course_id)
        formativas = qa.fetch_user_course_formative(aluno_id, course_id)
        quizz = qa.fetch_user_course_quizz(aluno_id, course_id)
        forum_criados = qa.fetch_user_forum_created_posts(aluno_id, course_id)
        forum_respostas = qa.fetch_user_forum_replies(aluno_id, course_id)
        
        # Valores fixos para volume de interação (ainda não pensei nas queries)
        volume_bloco = render_volume_interacao(50, 70, 25)

        progresso_global = qa.fetch_user_course_progress(aluno_id, course_id)
        performance = qa.fetch_user_course_performance(aluno_id, course_id)

    except Exception as e:
        print("Erro ao buscar progresso de atividades:", e)
        return html.Div("Erro ao ligar à base de dados.")

    return html.Div(className="dashboard-grid", children=[
        html.Div(className="coluna-esquerda", children=[
            render_progresso_atividades(avaliacao, formativas, quizz),
            render_mensagens_forum(forum_criados, forum_respostas),
            render_volume_interacao(50, 70, 25)
        ]),
        html.Div(className="coluna-direita", children=[
            render_progresso_global(progresso_global),
            render_performance(performance)
        ])
    ])

def render_progresso_atividades(avaliacao, formativas, quizz):
    return html.Div(className="card card-progresso", children=[
        html.H4("Progresso das Actividades", className="card-section-title"),

        # Avaliação — Amarelo
        barra_personalizada("Avaliação", avaliacao, "#e2f396"),
        # Formativas — Verde menta
        barra_personalizada("Formativas", formativas, "#76d19e"),
        # Quizz — Verde água escuro 
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

def render_volume_interacao(ficheiros, paginas, links):
    return html.Div(className="card card-volume", children=[
        html.H4("Volume de Interação", className="card-section-title"),
        html.Ul(className="volume-list", children=[

            html.Li(className="volume-item", children=[
                html.Div(className="volume-icon-bg bg-yellow", children=[
                    DashIconify(icon="mdi:folder-outline", width=24, color="white")
                ]),
                html.Span("Ficheiros"),
                html.Span(str(ficheiros), className="volume-number")
            ]),

            html.Li(className="volume-item", children=[
                html.Div(className="volume-icon-bg bg-green", children=[
                    DashIconify(icon="mdi:file-document-outline", width=24, color="white")
                ]),
                html.Span("Páginas"),
                html.Span(str(paginas), className="volume-number")
            ]),

            html.Li(className="volume-item", children=[
                html.Div(className="volume-icon-bg bg-darkgreen", children=[
                    DashIconify(icon="mdi:link-variant", width=24, color="white")
                ]),
                html.Span("Link"),
                html.Span(str(links), className="volume-number")
            ])
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
            'axis': {
                'range': [0, 100],
                'visible': False  # Oculta todos os ticks e traços
            },
            'bar': {'color': '#7cc3ac', 'thickness': 0.3},
            'bgcolor': "#f9f9f9",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 100], 'color': "#dfeeee"},
            ],
        }
    ))
    
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=160
    )
    return html.Div(className="card card-gauge", children=[
        html.H4("Progresso", className="card-section-title"),
        html.Div(className="gauge-wrapper", children=[
            dcc.Graph(figure=fig, config={'displayModeBar': False})
        ])
    ])

def render_performance(nivel):
    # Define classe com base no nível
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
