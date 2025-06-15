from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import queries.queriesGeral as qg
import queries.formsPre as qp
from utils.logger import logger


def register_callbacks(app):
    @app.callback(
        [Output("dropdown_item", "options"), Output("dropdown_item", "value")],
        Input("url", "pathname")
    )
    def carregar_opcoes_dropdown(_):
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

    @app.callback(
        Output("grafico_confianca_preparacao", "figure"),
        Input("dropdown_item", "value")
    )

    def atualizar_grafico(item_id):
        from queries.formsPre import pre_confianca_preparacao  # import local para evitar erro circular

        dados = pre_confianca_preparacao(item_id)

        df = pd.DataFrame(dados, columns=["item_id", "item_name", "categoria_preparacao", "total_respostas"])

        fig = px.pie(df, names="categoria_preparacao", values="total_respostas", hole=0.4,
                     color_discrete_sequence=["#f08080", "#ffd700", "#90ee90"])

        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20),
                          paper_bgcolor="#f4faf4", plot_bgcolor="#f4faf4", font=dict(color="#2c3e50"))

        return fig


# =========================
# DADOS MARTELADOS - APAGAR DEPOIS
# =========================

def get_valores_martelados_horas():
    return [3, 6, 9, 5, 2]

def get_valores_martelados_acessibilidade():
    return [5, 3, 2]

def get_valores_martelados_recursos():
    return [2, 4, 7, 3]

def get_valores_martelados_atividades():
    return [2, 3, 6, 2, 1] 

def get_total_respostas_martelado():
    total_respostas = 30
    total_alunos = 100
    return total_respostas, total_alunos
# =========================
# Layout principal
# =========================

def layout():
    # Obtém os valores martelados para os gráficos
    valores_horas = get_valores_martelados_horas()
    valores_aces = get_valores_martelados_acessibilidade()
    valores_rec = get_valores_martelados_recursos()
    valores_ativ = get_valores_martelados_atividades()

    return html.Div([

        html.Div([
            dcc.Dropdown(id="dropdown_item", placeholder="Seleciona o e-Fólio", className="dashboard-pre-dropdown")
        ], className="dashboard-pre-dropdown-wrapper"),

        html.H2("Grau de Confiança Pré-Efólio", className="dashboard-pre-subsecao"),
        render_total_respostas_info(),
        
        html.Div(className="dashboard-pre-row", children=[
            html.Div(className="dashboard-pre-card", children=[
                html.H4("Nível de preparação", className="dashboard-pre-card-title"),
                dcc.Graph(id="grafico_confianca_preparacao", config={"displayModeBar": False}, style={"height": "180px"})
            ]),
            render_grafico_horas_preparacao(valores_horas)
        ]),

        html.Div("Qualidade dos recursos", className="dashboard-pre-subtitulo"),

        html.Div(className="dashboard-pre-row", children=[
            render_grafico_acessibilidade(valores_aces),
            render_grafico_recursos(valores_rec),
            render_grafico_atividades(valores_ativ)
        ])
    ])



# =========================
# Componentes visuais
# =========================

def render_grafico_horas_preparacao(valores):
    categorias = ["Menos de 5h", "5 a 10h", "10 a 20h", "20 a 40h", "Mais de 40h"]
    cores = ["#f9e79f", "#dcdcdc", "#2c7873", "#76d7c4", "#aed6f1"]

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
        height=200,
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        yaxis=dict(autorange="reversed")
    )

    return html.Div(className="dashboard-pre-card", children=[
        html.H4("Nº Horas de Preparação", className="dashboard-pre-card-title"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "180px"})
    ])

def render_grafico_acessibilidade(valores):
    categorias = [
        "Simples e acessível",
        "Essencial acessível",
        "Dificuldade na navegação"
    ]
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

    return html.Div(className="dashboard-pre-card", children=[
        html.H4("Acessibilidade", className="dashboard-pre-card-title"),
        html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
        ])
    ])

def render_grafico_recursos(valores):
    categorias = [
        "Não utilizei/encontrei",
        "Alguma utilidade",
        "Bem estruturados e úteis",
        "Pouco claros ou desatualizados"
    ]
    cores = ["#d3d3d3", "#ffe066", "#8cd17d", "#ffb3b3"]

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

    return html.Div(className="dashboard-pre-card", children=[
        html.H4("Assertividade", className="dashboard-pre-card-title"),
        html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
        ])
    ])


def render_grafico_atividades(valores):
    categorias = [
        "Correção não ajudou",
        "Desatualizadas/irrelevantes",
        "Claras e úteis",
        "Lacunas ou pouco claras",
        "Não encontrei/fiz"
    ]
    cores = ["#f7c59f", "#ffeb99", "#90ee90", "#ff9999", "#d3d3d3"]

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

    return html.Div(className="dashboard-pre-card", children=[
        html.H4("Atividades Formativas", className="dashboard-pre-card-title"),
        html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
        ])
    ])



def render_total_respostas_info():
    total_respostas, total_alunos = get_total_respostas_martelado()
    texto = f"{total_respostas} respostas de {total_alunos} alunos"
    return html.P(texto, className="dashboard-pre-info-respostas")
