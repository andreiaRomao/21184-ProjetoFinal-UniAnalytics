from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import queries.queriesComuns as qg
from utils.logger import logger
import queries.formsPos as qpos
import queries.formsComuns as qfcomuns


# =========================
# Funções de lógica modular
# ========================
def register_callbacks(app):
    @app.callback(
        [Output("dropdown_item_pos", "options"), Output("dropdown_item_pos", "value")],
        Input("url", "pathname")
    )
    def carregar_opcoes_dropdown(_):
        return obter_opcoes_dropdown_pos()

    @app.callback(
        Output("grafico_confianca_pos", "figure"),
        Output("grafico_horas_pos", "figure"),
        Output("grafico_expectativa", "children"),
        Output("grafico_dificuldade", "children"),
        Output("grafico_esforco", "children"),
        Output("grafico_abrangencia", "children"),
        Output("grafico_sincrona", "children"),
        Output("info_total_respostas_pos", "children"),
        Input("dropdown_item_pos", "value")
    )
    def atualizar_grafico(item_id):
        valores_horas = get_valores_reais_horas_pos(item_id)
        valores_exp = get_valores_reais_expectativa(item_id)
        valores_dif = get_valores_reais_dificuldade(item_id)
        valores_esf = get_valores_reais_esforco(item_id)
        valores_abr = get_valores_reais_abrangencia(item_id)
        valores_sin = get_valores_reais_sincrona(item_id)
        return (
            render_grafico_confianca_pos(item_id),
            render_grafico_horas_pos(valores_horas),
            render_grafico_expectativa(valores_exp),
            render_grafico_dificuldade(valores_dif),
            render_grafico_esforco(valores_esf),
            render_grafico_abrangencia(valores_abr),
            render_grafico_sincrona(valores_sin),
            render_total_respostas_info_reais(item_id)
        )

def obter_opcoes_dropdown_pos():
    try:
        logger.debug("[DASHBOARD_POS] A carregar opções para dropdown_item_pos")

        resultados = qfcomuns.fetch_all_efolios_local()
        logger.debug(f"[DASHBOARD_POS] Resultados fetch_all_efolios: {resultados}")

        df = pd.DataFrame(resultados)
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
        df['ano_letivo'] = df['start_date'].dt.year
        ano_mais_recente = df['ano_letivo'].max()

        logger.debug(f"[DASHBOARD_POS] Ano letivo mais recente: {ano_mais_recente}")
        df_filtrado = df[df['ano_letivo'] == ano_mais_recente]

        opcoes = [{
            "label": f"{row['name']} ({row['start_date'].strftime('%Y-%m-%d')} a {row['end_date'].strftime('%Y-%m-%d')})",
            "value": row["item_id"]
        } for _, row in df_filtrado.iterrows()]

        valor_default = opcoes[0]['value'] if opcoes else None
        logger.debug(f"[DASHBOARD_POS] Opções filtradas: {opcoes}")

        return opcoes, valor_default

    except Exception as e:
        logger.exception("[DASHBOARD_POS] Erro ao carregar opções para dropdown")
        return [], None

def get_total_respostas_info_reais(item_id):
    try:
        course_id, total_respostas = qfcomuns.pre_pos_obter_course_id_e_total_respostas(item_id)
        if not course_id:
            return "Curso não encontrado."

        df_utilizadores = pd.DataFrame(qg.fetch_all_user_course_data_local())

        df_filtrado = df_utilizadores[
            (df_utilizadores["role"].str.lower() == "student") &
            (df_utilizadores["course_id"] == course_id) &
            (df_utilizadores["group_name"].fillna("").str.strip().str.lower().str.contains("aval"))
        ]

        total_alunos = len(df_filtrado)

        logger.debug(f"[DASHBOARD_POS] Total respostas: {total_respostas}, Total alunos: {total_alunos}")
        return f"{total_respostas} respostas de {total_alunos} alunos"

    except Exception as e:
        logger.exception("[DASHBOARD_POS] Erro ao obter dados reais")
        return "Erro ao obter dados reais"

def get_valores_reais_horas_pos(item_id):
    dados = qpos.pos_horas_dedicadas(item_id)

    ordem_desejada = [
        "Menos de 2h",
        "Entre 2h a 5h",
        "Entre 5h a 10h",
        "Mais de 10h"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}

    for _, _, categoria, total in dados:
        contagem[categoria] += total

    logger.debug(f"[DASHBOARD_POS] Horas dedicadas: {contagem}")
    return contagem

def get_valores_reais_expectativa(item_id):
    dados = qpos.pos_expectativa_desempenho(item_id)

    ordem_desejada = [
        "Expectativa elevada",
        "Expectativa moderada",
        "Expectativa positiva",
        "Expectativa muito baixa"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}
    for _, _, categoria, total in dados:
        contagem[categoria] += total

    logger.debug(f"[DASHBOARD_POS] Expectativa desempenho: {contagem}")
    return contagem

def get_valores_reais_dificuldade(item_id):
    dados = qpos.pos_dificuldade_efolio(item_id)

    ordem_desejada = [
        "Difícil",
        "Fácil",
        "Moderado"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}
    for _, _, categoria, total in dados:
        contagem[categoria] += total

    logger.debug(f"[DASHBOARD_POS] Dificuldade eFólio: {contagem}")
    return contagem

def get_valores_reais_esforco(item_id):
    dados = qpos.pos_esforco_investido(item_id)

    ordem_desejada = [
        "Esforço razoável",
        "Esforço insuficiente",
        "Esforço máximo"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}
    for _, _, categoria, total in dados:
        contagem[categoria] += total

    logger.debug(f"[DASHBOARD_POS] Esforço investido: {contagem}")
    return contagem

def get_valores_reais_abrangencia(item_id):
    dados = qpos.pos_recursos_qualidade(item_id)

    ordem_desejada = [
        "Não cobriram os tópicos",
        "Parcialmente cobriram",
        "Cobriram adequadamente"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}
    for _, _, categoria, total in dados:
        contagem[categoria] += total

    logger.debug(f"[DASHBOARD_POS] Abrangência dos recursos: {contagem}")
    return contagem

def get_valores_reais_sincrona(item_id):
    dados = qpos.pos_sessao_sincrona_qualidade(item_id)

    ordem_desejada = [
        "Muito útil",
        "Útil, mas com lacunas",
        "Não aplicável",
        "Não foi útil"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}
    for _, _, categoria, total in dados:
        contagem[categoria] += total

    logger.debug(f"[DASHBOARD_POS] Sessão síncrona: {contagem}")
    return contagem

# =========================
# Layout principal
# =========================

def layout():

    return html.Div([
        html.Div([
            dcc.Dropdown(id="dropdown_item_pos", placeholder="Seleciona o e-Fólio", className="dashboard-pre-dropdown")
        ], className="dashboard-pre-dropdown-wrapper"),

        html.H2("Reflexão sobre a avaliação", className="dashboard-pre-subsecao"),
        html.Div(id="info_total_respostas_pos"),

        html.Div(className="dashboard-pre-row", children=[
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Nível de preparação", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Mostra como os alunos classificaram o seu nível de preparação antes do e-fólio.\n"
                        "Inclui categorias como:\n"
                        "- Pouco preparado\n"
                        "- Razoavelmente preparado\n"
                        "- Muito preparado",
                        className="tooltip-text"
                    )
                ]),
                dcc.Graph(id="grafico_confianca_pos", config={"displayModeBar": False}, style={"height": "180px"})
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Nº de horas dedicadas", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Mostra o tempo total dedicado à realização do e-fólio por parte do aluno.\n"
                        "Categorias consideradas:\n"
                        "- Menos de 2h\n"
                        "- Entre 2h a 5h\n"
                        "- Entre 5h a 10h\n"
                        "- Mais de 10h",
                        className="tooltip-text"
                    )
                ]),
                dcc.Graph(id="grafico_horas_pos", config={"displayModeBar": False}, style={"height": "180px"})
            ])
        ]),
        html.Div(className="dashboard-pre-row", children=[
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Expectativa desempenho [Nota]", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Mostra a expectativa dos alunos em relação ao seu próprio desempenho no e-fólio, em termos de nota esperada.\n"
                        "Categorias disponíveis:\n"
                        "- Expectativa elevada\n"
                        "- Expectativa moderada\n"
                        "- Expectativa positiva\n"
                        "- Expectativa muito baixa",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_expectativa")
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Grau de dificuldade", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Mostra a perceção dos alunos sobre o grau de dificuldade do e-fólio.\n"
                        "Categorias possíveis:\n"
                        "- Fácil\n"
                        "- Moderado\n"
                        "- Difícil",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_dificuldade")
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Esforço investido", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Reflete o nível de esforço dedicado pelo aluno na realização do e-fólio.\n"
                        "Categorias possíveis:\n"
                        "- Esforço máximo\n"
                        "- Esforço razoável\n"
                        "- Esforço insuficiente",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_esforco")
            ])
        ]),
        html.Div("Qualidade dos recursos", className="dashboard-pre-subtitulo"),

        html.Div(className="dashboard-pre-row", children=[
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Abrangência", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Reflete se os recursos e conteúdos disponibilizados cobriram adequadamente os tópicos exigidos no e-fólio.\n"
                        "Categorias possíveis:\n"
                        "- Cobriram adequadamente\n"
                        "- Parcialmente cobriram\n"
                        "- Não cobriram os tópicos",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_abrangencia")
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Sessão Síncrona", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Reflete a perceção sobre a utilidade da sessão síncrona associada ao e-fólio.\n"
                        "Categorias possíveis:\n"
                        "- Muito útil\n"
                        "- Útil, mas com lacunas\n"
                        "- Não foi útil\n"
                        "- Não aplicável",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_sincrona")
            ])
        ])
    ])

# =========================
# Componentes visuais
# =========================

def render_total_respostas_info_pos():
    total_respostas, total_alunos = 28, 92  # ← martelado para já
    texto = f"{total_respostas} respostas de {total_alunos} alunos"
    return html.P(texto, className="dashboard-pre-info-respostas")

def render_grafico_confianca_pos(item_id):    
    dados = qpos.pos_confianca_preparacao(item_id)

    df = pd.DataFrame(dados, columns=["item_id", "item_name", "categoria_pos_preparacao", "total_respostas"])

    if df.empty or df["total_respostas"].sum() == 0:
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="Sem dados suficientes para gerar o gráfico.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="#2c3e50")
                )
            ],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            paper_bgcolor="#f4faf4",
            plot_bgcolor="#f4faf4",
            margin=dict(l=10, r=10, t=20, b=10)
        )
        return fig

    fig = px.pie(
        df,
        names="categoria_pos_preparacao",
        values="total_respostas",
        hole=0.4,
        color_discrete_sequence=["#f08080", "#ffd700", "#90ee90"]
    )
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50")
    )
    return fig

def render_grafico_horas_pos(valores_dict):
    categorias = ["Menos de 2h", "Entre 2h a 5h", "Entre 5h a 10h", "Mais de 10h"]
    cores = ["#f7c59f", "#f9e79f", "#dcdcdc", "#aed6f1"]
    valores = [valores_dict.get(cat, 0) for cat in categorias]

    # Se todos os valores forem 0, mostrar mensagem dentro do gráfico
    if all(val == 0 for val in valores):
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="Sem dados suficientes para gerar o gráfico.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="#2c3e50")
                )
            ],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            paper_bgcolor="#f4faf4",
            plot_bgcolor="#f4faf4",
            height=180
        )
        return fig

    # Caso normal
    fig = go.Figure(go.Bar(
        x=valores,
        y=categorias,
        orientation='h',
        marker=dict(color=cores),
        text=valores,
        textposition="auto"
    ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=180,
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        yaxis=dict(autorange="reversed"),
        font=dict(color="#2c3e50")
    )

    return fig

def render_grafico_expectativa(valores_dict):
    categorias = [
        "Expectativa elevada",
        "Expectativa moderada",
        "Expectativa positiva",
        "Expectativa muito baixa"
    ]
    cores = ["#90ee90", "#ffd700", "#87CEEB", "#f08080"]

    # Filtrar categorias com valor > 0
    indices_validos = [i for i, cat in enumerate(categorias) if valores_dict.get(cat, 0) > 0]
    categorias = [categorias[i] for i in indices_validos]
    valores = [valores_dict[categorias[i]] for i in range(len(categorias))]
    cores = [cores[i] for i in indices_validos]

    if not categorias:
        return html.Div("Sem dados suficientes para gerar o gráfico.", style={"textAlign": "center", "padding": "20px"})

    fig = px.pie(
        names=categorias,
        values=valores,
        hole=0.4,
        color_discrete_sequence=cores
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=0, l=20, r=20),
        height=200,
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50")
    )

    legenda = html.Div(className="dashboard-pre-legenda-2colunas", children=[
        html.Div([
            html.Span(style={"backgroundColor": cores[i]}, className="dashboard-pre-legenda-cor"),
            html.Span(categorias[i])
        ], className="dashboard-pre-legenda-item") for i in range(len(categorias))
    ])

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
    ])

def render_grafico_dificuldade(valores_dict):
    categorias = [
        "Difícil",
        "Fácil",
        "Moderado"
    ]
    cores = ["#f08080", "#90ee90", "#ffd700"]

    # Filtrar categorias com valor > 0
    indices_validos = [i for i, cat in enumerate(categorias) if valores_dict.get(cat, 0) > 0]
    categorias = [categorias[i] for i in indices_validos]
    valores = [valores_dict[categorias[i]] for i in range(len(categorias))]
    cores = [cores[i] for i in indices_validos]

    if not categorias:
        return html.Div("Sem dados suficientes para gerar o gráfico.", style={"textAlign": "center", "padding": "20px"})

    fig = px.pie(
        names=categorias,
        values=valores,
        hole=0.4,
        color_discrete_sequence=cores
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=0, l=20, r=20),
        height=200,
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50")
    )

    legenda = html.Div(className="dashboard-pre-legenda-2colunas", children=[
        html.Div([
            html.Span(style={"backgroundColor": cores[i]}, className="dashboard-pre-legenda-cor"),
            html.Span(categorias[i])
        ], className="dashboard-pre-legenda-item") for i in range(len(categorias))
    ])

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
        legenda
    ])


def render_grafico_esforco(valores_dict):
    categorias = [
        "Esforço razoável",
        "Esforço insuficiente",
        "Esforço máximo"
    ]
    cores = ["#ffd700", "#f08080", "#90ee90"]

    # Filtrar categorias com valor > 0
    indices_validos = [i for i, cat in enumerate(categorias) if valores_dict.get(cat, 0) > 0]
    categorias = [categorias[i] for i in indices_validos]
    valores = [valores_dict[categorias[i]] for i in range(len(categorias))]
    cores = [cores[i] for i in indices_validos]

    if not categorias:
        return html.Div("Sem dados suficientes para gerar o gráfico.", style={"textAlign": "center", "padding": "20px"})

    fig = px.pie(
        names=categorias,
        values=valores,
        hole=0.4,
        color_discrete_sequence=cores
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=0, l=20, r=20),
        height=200,
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50")
    )

    legenda = html.Div(className="dashboard-pre-legenda-2colunas", children=[
        html.Div([
            html.Span(style={"backgroundColor": cores[i]}, className="dashboard-pre-legenda-cor"),
            html.Span(categorias[i])
        ], className="dashboard-pre-legenda-item") for i in range(len(categorias))
    ])

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
        legenda
    ])


def render_grafico_abrangencia(valores_dict):
    categorias = [
        "Não cobriram os tópicos",
        "Parcialmente cobriram",
        "Cobriram adequadamente"
    ]
    cores = ["#f08080", "#ffd700", "#90ee90"]

    # Filtrar categorias com valor > 0
    indices_validos = [i for i, cat in enumerate(categorias) if valores_dict.get(cat, 0) > 0]
    categorias = [categorias[i] for i in indices_validos]
    valores = [valores_dict[categorias[i]] for i in range(len(categorias))]
    cores = [cores[i] for i in indices_validos]

    if not categorias:
        return html.Div("Sem dados suficientes para gerar o gráfico.", style={"textAlign": "center", "padding": "20px"})

    fig = px.pie(
        names=categorias,
        values=valores,
        hole=0.4,
        color_discrete_sequence=cores
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=0, l=20, r=20),
        height=200,
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50")
    )

    legenda = html.Div(className="dashboard-pre-legenda-2colunas", children=[
        html.Div([
            html.Span(style={"backgroundColor": cores[i]}, className="dashboard-pre-legenda-cor"),
            html.Span(categorias[i])
        ], className="dashboard-pre-legenda-item") for i in range(len(categorias))
    ])

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
        legenda
    ])

def render_grafico_sincrona(valores_dict):
    categorias = [
        "Muito útil",
        "Útil, mas com lacunas",
        "Não aplicável",
        "Não foi útil"
    ]
    cores = ["#90ee90", "#ffd700", "#d3d3d3", "#f08080"]

    # Filtrar categorias com valor > 0
    indices_validos = [i for i, cat in enumerate(categorias) if valores_dict.get(cat, 0) > 0]
    categorias = [categorias[i] for i in indices_validos]
    valores = [valores_dict[categorias[i]] for i in range(len(categorias))]
    cores = [cores[i] for i in indices_validos]

    if not categorias:
        return html.Div("Sem dados suficientes para gerar o gráfico.", style={"textAlign": "center", "padding": "20px"})

    fig = px.pie(
        names=categorias,
        values=valores,
        hole=0.4,
        color_discrete_sequence=cores
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=0, l=20, r=20),
        height=200,
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50")
    )

    legenda = html.Div(className="dashboard-pre-legenda-2colunas", children=[
        html.Div([
            html.Span(style={"backgroundColor": cores[i]}, className="dashboard-pre-legenda-cor"),
            html.Span(categorias[i])
        ], className="dashboard-pre-legenda-item") for i in range(len(categorias))
    ])

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
        legenda
    ])

def render_total_respostas_info_reais(item_id):
    texto = get_total_respostas_info_reais(item_id)
    return html.P(texto, className="dashboard-pre-info-respostas")