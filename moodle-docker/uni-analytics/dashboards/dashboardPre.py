from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import queries.queriesGeral as qg
import queries.formsPre as qpre
import queries.formsGeral as qfgeral
from utils.logger import logger


def register_callbacks(app):
    @app.callback(
        [Output("dropdown_item", "options"), Output("dropdown_item", "value")],
        Input("url", "pathname")
    )
    def carregar_opcoes_dropdown(_):
        return obter_opcoes_dropdown_pre()

    @app.callback(
        Output("grafico_confianca_preparacao", "figure"),
        Output("grafico_horas_preparacao", "figure"),
        Output("grafico_acessibilidade", "children"),
        Output("grafico_assertividade", "children"),
        Output("grafico_atividades", "children"),
        Output("info_total_respostas_pre", "children"),
        Input("dropdown_item", "value")
    )
    def atualizar_grafico(item_id):
        valores_horas = get_valores_reais_horas(item_id)
        valores_aces = get_valores_reais_acessibilidade(item_id) 
        valores_assert = get_valores_reais_assertividade(item_id)
        valores_ativ = get_valores_reais_atividades(item_id)
        return (
            gerar_grafico_confianca_pre(item_id), 
            render_grafico_horas_preparacao(valores_horas),
            render_grafico_acessibilidade(valores_aces),
            render_grafico_recursos(valores_assert),
            render_grafico_atividades(valores_ativ),
            render_total_respostas_info_reais(item_id)
        )


def obter_opcoes_dropdown_pre():
    try:
        logger.debug("[DASHBOARD_PRE] A carregar opções para dropdown_item")

        resultados = qg.fetch_all_efolios()
        logger.debug(f"[DASHBOARD_PRE] Resultados fetch_all_efolios: {resultados}")

        df = pd.DataFrame(resultados)
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['ano_letivo'] = df['start_date'].dt.year
        ano_mais_recente = df['ano_letivo'].max()

        logger.debug(f"[DASHBOARD_PRE] Ano letivo mais recente: {ano_mais_recente}")
        df_filtrado = df[df['ano_letivo'] == ano_mais_recente]

        opcoes = [{
            "label": f"{row['name']} ({row['start_date'].strftime('%Y-%m-%d')} a {row['end_date'].strftime('%Y-%m-%d')})",
            "value": row["item_id"]
        } for _, row in df_filtrado.iterrows()]

        valor_default = opcoes[0]['value'] if opcoes else None
        logger.debug(f"[DASHBOARD_PRE] Opções filtradas: {opcoes}")

        return opcoes, valor_default

    except Exception as e:
        logger.exception("[DASHBOARD_PRE] Erro ao carregar opções para dropdown")
        return [], None

def get_total_respostas_info_reais(item_id):
    try:
        # Obtemos o course_id e o total de respostas do forms
        course_id, total_respostas = qfgeral.pre_pos_obter_course_id_e_total_respostas(item_id)
        if not course_id:
            return "Curso não encontrado."

        # Obtemos a lista de utilizadores inscritos nesse curso
        df_utilizadores = qg.fetch_user_course_data()

        # Filtramos alunos da Avaliação Contínua naquele curso
        df_filtrado = df_utilizadores[
            (df_utilizadores["role"].str.lower() == "student") &
            (df_utilizadores["courseid"] == course_id) &
            (df_utilizadores["groupname"].fillna("").str.strip().str.lower().str.contains("aval"))
        ]

        total_alunos = len(df_filtrado)

        return f"{total_respostas} respostas de {total_alunos} alunos"
    
    except Exception as e:
        return "Erro ao obter dados reais"


def gerar_grafico_confianca_pre(item_id):
    dados = qpre.pre_confianca_preparacao(item_id)

    df = pd.DataFrame(dados, columns=["item_id", "item_name", "categoria_preparacao", "total_respostas"])

    fig = px.pie(
        df,
        names="categoria_preparacao",
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


def get_valores_reais_horas(item_id):
    ordem_desejada = ["< 5h", "5 a 10h", "10 a 20h", "20 a 40h", "> 40h"]

    dados = qpre.pre_horas_preparacao(item_id)

    contagem = {cat: 0 for cat in ordem_desejada}

    for _, _, categoria, total in dados:
        contagem[categoria] = total

    return contagem

def get_valores_reais_acessibilidade(item_id):
    dados = qpre.pre_recursos_acessibilidade(item_id)

    ordem_desejada = [
        "Acessíveis e bem organizados",
        "Acessíveis, mas estrutura confusa",
        "Pouco acessíveis e desorganizados"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}
    for _, _, categoria, total in dados:
        contagem[categoria] += total

    return contagem

def get_valores_reais_assertividade(item_id):
    dados = qpre.pre_recursos_utilidade(item_id)

    ordem_desejada = [
        "Não utilizados",
        "Parcialmente úteis - lacunas",
        "Muito úteis",
        "Pouco úteis - Necessitam revisao"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}
    for _, _, categoria, total in dados:
        contagem[categoria] += total

    return contagem


def get_valores_reais_atividades(item_id):
    dados = qpre.pre_atividades_utilidade(item_id)

    ordem_desejada = [
        "Parcialmente úteis - correção",
        "Parcialmente úteis - desatualizadas",
        "Muito úteis",
        "Parcialmente úteis - lacunas",
        "Não realizou"
    ]

    contagem = {cat: 0 for cat in ordem_desejada}
    for _, _, categoria, total in dados:
        contagem[categoria] += total

    return contagem

# =========================
# Layout principal
# =========================

def layout():

    return html.Div([

        html.Div([
            dcc.Dropdown(id="dropdown_item", placeholder="Seleciona o e-Fólio", className="dashboard-pre-dropdown")
        ], className="dashboard-pre-dropdown-wrapper"),

        html.H2("Grau de Confiança Pré-Efólio", className="dashboard-pre-subsecao"),
        html.Div(id="info_total_respostas_pre"),
        
        html.Div(className="dashboard-pre-row", children=[
            html.Div(className="dashboard-pre-card", children=[
                html.H4("Nível de preparação", className="dashboard-pre-card-title"),
                dcc.Graph(id="grafico_confianca_preparacao", config={"displayModeBar": False}, style={"height": "180px"})
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.H4("Nº Horas de Preparação", className="dashboard-pre-card-title"),
                dcc.Graph(id="grafico_horas_preparacao", config={"displayModeBar": False}, style={"height": "180px"})
            ])
        ]),

        html.Div("Qualidade dos recursos", className="dashboard-pre-subtitulo"),

        html.Div(className="dashboard-pre-row", children=[
            html.Div(className="dashboard-pre-card", children=[
                html.H4("Acessibilidade", className="dashboard-pre-card-title"),
                html.Div(id="grafico_acessibilidade")
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.H4("Assertividade", className="dashboard-pre-card-title"),
                html.Div(id="grafico_assertividade")
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.H4("Atividades Formativas", className="dashboard-pre-card-title"),
                html.Div(id="grafico_atividades")
            ])
        ])
    ])

# =========================
# Componentes visuais
# =========================

def render_grafico_horas_preparacao(valores_dict):
    ordem_desejada = ["< 5h", "5 a 10h", "10 a 20h", "20 a 40h", "> 40h"]
    cores = ["#f9e79f", "#dcdcdc", "#2c7873", "#76d7c4", "#aed6f1"]

    categorias = ordem_desejada
    valores = [valores_dict.get(cat, 0) for cat in categorias]

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

def render_grafico_acessibilidade(valores_dict):
    categorias = [
        "Acessíveis e bem organizados",
        "Acessíveis, mas estrutura confusa",
        "Pouco acessíveis e desorganizados"
    ]
    valores = [valores_dict.get(cat, 0) for cat in categorias]
    cores = ["#90ee90", "#ffd700", "#f08080"]

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

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px", "minHeight": "300px" }, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        legenda
    ])

def render_grafico_recursos(valores_dict):
    categorias = [
        "Não utilizados",
        "Parcialmente úteis - lacunas",
        "Muito úteis",
        "Pouco úteis - Necessitam revisao"
    ]
    cores = ["#d3d3d3", "#ffe066", "#8cd17d", "#ffb3b3"]
    valores = [valores_dict.get(cat, 0) for cat in categorias]

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

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px", "minHeight": "300px"}, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        legenda
    ])

def render_grafico_atividades(valores_dict):
    categorias = [
        "Parcialmente úteis - correção",
        "Parcialmente úteis - desatualizadas",
        "Muito úteis",
        "Parcialmente úteis - lacunas",
        "Não realizou"
    ]
    cores = ["#f7c59f", "#ffeb99", "#90ee90", "#ff9999", "#d3d3d3"]
    valores = [valores_dict.get(cat, 0) for cat in categorias]

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

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px", "minHeight": "300px"}, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        legenda
    ])

def render_total_respostas_info_reais(item_id):
    texto = get_total_respostas_info_reais(item_id)
    return html.P(texto, className="dashboard-pre-info-respostas")
