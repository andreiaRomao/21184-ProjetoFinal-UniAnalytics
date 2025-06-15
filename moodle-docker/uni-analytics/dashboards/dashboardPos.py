from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import queries.queriesGeral as qg
import queries.formsPos as qp
from utils.logger import logger



def register_callbacks(app):
    @app.callback(
        [Output("dropdown_item_pos", "options"), Output("dropdown_item_pos", "value")],
        Input("url", "pathname")
    )
    def carregar_opcoes_dropdown(_):
        try:
            logger.debug("[DASHBOARD_POS] A carregar opções para dropdown_item_pos")

            resultados = qg.fetch_all_efolios()
            logger.debug(f"[DASHBOARD_POS] Resultados fetch_all_efolios: {resultados}")

            df = pd.DataFrame(resultados)
            df['start_date'] = pd.to_datetime(df['start_date'])
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

    @app.callback(
        Output("grafico_confianca_pos", "figure"),
        Input("dropdown_item_pos", "value")
    )
    def atualizar_grafico(item_id):
        from queries.formsPos import pos_confianca_preparacao
        dados = pos_confianca_preparacao(item_id)
        df = pd.DataFrame(dados, columns=["item_id", "item_name", "categoria_pos_preparacao", "total_respostas"])
        fig = px.pie(df, names="categoria_pos_preparacao", values="total_respostas", hole=0.4,
                     color_discrete_sequence=["#87CEEB", "#FFA07A", "#9370DB"])
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20),
                          paper_bgcolor="#f4faf4", plot_bgcolor="#f4faf4", font=dict(color="#2c3e50"))
        return fig

# =========================
# DADOS MARTELADOS - APAGAR DEPOIS
# =========================

def get_total_respostas_martelado():
    total_respostas = 30
    total_alunos = 100
    return total_respostas, total_alunos

def get_valores_martelados_horas_pos():
    return [2, 4, 7, 3, 1] 

def get_valores_martelados_expectativa():
    return [4, 6, 12, 6] 

def get_valores_martelados_dificuldade():
    return [5, 10, 13]  

def get_valores_martelados_esforco():
    return [8, 7, 13]  

def get_valores_martelados_abrangencia():
    return [4, 9, 15]

def get_valores_martelados_sincrona():
    return [10, 6, 8, 4]
# =========================
# Layout principal
# =========================

def layout():
    valores_horas = get_valores_martelados_horas_pos() # ← martelado para já
    valores_expectativa = get_valores_martelados_expectativa()
    valores_dificuldade = get_valores_martelados_dificuldade()
    valores_esforço = get_valores_martelados_esforco()
    valores_abrangencia = get_valores_martelados_abrangencia()
    valores_sincrona = get_valores_martelados_sincrona()

    return html.Div([
        html.Div([
            dcc.Dropdown(id="dropdown_item_pos", placeholder="Seleciona o e-Fólio", className="dashboard-pre-dropdown")
        ], className="dashboard-pre-dropdown-wrapper"),

        html.H2("Reflexão sobre a avaliação", className="dashboard-pre-subsecao"),
        render_total_respostas_info_pos(),

        html.Div(className="dashboard-pre-row", children=[
            html.Div(className="dashboard-pre-card", children=[
                html.H4("Nível de preparação", className="dashboard-pre-card-title"),
                dcc.Graph(id="grafico_confianca_pos", config={"displayModeBar": False}, style={"height": "180px"})
            ]),
            render_grafico_horas_pos(valores_horas)
        ]),
        html.Div(className="dashboard-pre-row", children=[
            render_grafico_expectativa(valores_expectativa),
            render_grafico_dificuldade(valores_dificuldade),
            render_grafico_esforco(valores_esforço)
        ]),
        html.Div("Qualidade dos recursos", className="dashboard-pre-subtitulo"),

        html.Div(className="dashboard-pre-row", children=[
            render_grafico_abrangencia(valores_abrangencia),
            render_grafico_sincrona(valores_sincrona)
        ])
    ])

# =========================
# Componentes visuais
# =========================

def render_total_respostas_info_pos():
    total_respostas, total_alunos = 28, 92  # ← martelado para já
    texto = f"{total_respostas} respostas de {total_alunos} alunos"
    return html.P(texto, className="dashboard-pre-info-respostas")

def render_grafico_horas_pos(valores):
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
        html.H4("Nº de horas dedicadas", className="dashboard-pre-card-title"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "180px"})
    ])

def render_grafico_expectativa(valores):
    categorias = [
        "Espera nota muito alta",
        "Expectativa moderada",
        "Confiante no geral",
        "Espera nota baixa"
    ]
    cores = ["#90ee90", "#ffd700", "#87CEEB", "#f08080"]

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
        html.H4("Expectativa desempenho [Nota]", className="dashboard-pre-card-title"),
        html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
        ])
    ])


def render_grafico_dificuldade(valores):
    categorias = [
        "Difícil e desadequado",
        "Fácil e confiante",
        "Moderado, com esforço"
    ]
    cores = ["#f08080", "#90ee90", "#ffd700"]

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
        html.H4("Grau de dificuldade", className="dashboard-pre-card-title"),
        html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
        ])
    ])

def render_grafico_esforco(valores):
    categorias = [
        "Esforço razoável",
        "Esforço insuficiente",
        "Esforço total"
    ]
    cores = ["#ffd700", "#f08080", "#90ee90"]

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
        html.H4("Esforço investido", className="dashboard-pre-card-title"),
        html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
        ])
    ])

def render_grafico_abrangencia(valores):
    categorias = [
        "Não cobre os temas",
        "Parcial",
        "Cobre bem os temas"
    ]
    cores = ["#f08080", "#ffd700", "#90ee90"]

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
        html.H4("Abrangência", className="dashboard-pre-card-title"),
        html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
        ])
    ])

def render_grafico_sincrona(valores):
    categorias = [
        "Muito útil",
        "Útil, com lacunas",
        "Não existiu",
        "Não foi útil"
    ]
    cores = ["#90ee90", "#ffd700", "#d3d3d3", "#f08080"]

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
        html.H4("Sessão Síncrona", className="dashboard-pre-card-title"),
        html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px"}, children=[
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "200px"}),
            legenda
        ])
    ])
