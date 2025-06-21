from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import queries.queriesComuns as qg
import queries.formsPre as qpre
import queries.formsComuns as qfcomuns
import re
from utils.logger import logger
from db.uniAnalytics import connect_to_uni_analytics_db

# =========================
# DADOS MARTELADOS APAGAR!!!!
# ========================

def get_valores_martelados_sessao_sincrona_pre():
    return {
        "Muito útil": 35,
        "Útil, mas com lacunas": 18,
        "Não foi útil": 4,
        "Ainda não se realizou": 12
    }

# =========================
# Funções de lógica modular
# ========================

def register_callbacks(app):
    @app.callback(
        [Output("dropdown_item", "options"), Output("dropdown_item", "value")],
        Input("url", "pathname")
    )
    def carregar_opcoes_dropdown(_):
        return obter_opcoes_dropdown_pre()

    @app.callback(
        Output("barra_superior_formulario", "children"),
        Output("grafico_confianca_preparacao", "figure"),
        Output("grafico_horas_preparacao", "figure"),
        Output("grafico_acessibilidade", "children"),
        Output("grafico_assertividade", "children"),
        Output("grafico_atividades", "children"),
        Output("grafico_sessao_sincrona_pre", "children"),
        Output("info_total_respostas_pre", "children"),
        Input("dropdown_item", "value")
    )
    def atualizar_grafico(item_id):
        logger.debug(f"[DASHBOARD_PRE] Atualizar gráficos para item_id: {item_id}")
        valores_horas = get_valores_reais_horas(item_id)
        valores_aces = get_valores_reais_acessibilidade(item_id) 
        valores_assert = get_valores_reais_assertividade(item_id)
        valores_ativ = get_valores_reais_atividades(item_id)
        return (
            render_barra_uc_form(item_id),
            render_grafico_confianca_pre(item_id), 
            render_grafico_horas_preparacao(valores_horas),
            render_grafico_acessibilidade(valores_aces),
            render_grafico_recursos(valores_assert),
            render_grafico_atividades(valores_ativ),
            render_grafico_sessao_sincrona_pre(get_valores_martelados_sessao_sincrona_pre()),
            render_total_respostas_info_reais(item_id)
        )

def obter_opcoes_dropdown_pre():
    try:
        logger.debug("[DASHBOARD_PRE] A carregar opções para dropdown_item")

        resultados = qfcomuns.fetch_all_efolios_local()
        logger.debug(f"[DASHBOARD_PRE] Resultados fetch_all_efolios: {resultados}")

        df = pd.DataFrame(resultados)
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
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

def extrair_ano_letivo(course_name):
    match = re.search(r'_(\d{2})', course_name)
    if match:
        sufixo = int(match.group(1))
        ano_inicio = 2000 + sufixo
        return f"{ano_inicio}/{ano_inicio + 1}"
    return None

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

        return f"{total_respostas} respostas de {total_alunos} alunos"

    except Exception as e:
        logger.exception("[DASHBOARD_PRE] Erro ao obter dados reais")
        return "Erro ao obter dados reais"

def get_valores_reais_horas(item_id):
    dados = qpre.pre_horas_preparacao(item_id)
    ordem_desejada = ["< 5h", "5 a 10h", "10 a 20h", "20 a 40h", "> 40h"]
    contagem = {cat: 0 for cat in ordem_desejada}

    for _, _, categoria, total in dados:
        contagem[categoria] = total

    logger.debug(f"[DASHBOARD_PRE] Horas preparação: {contagem}")
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

    logger.debug(f"[DASHBOARD_PRE] Acessibilidade: {contagem}")
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

    logger.debug(f"[DASHBOARD_PRE] Assertividade: {contagem}")
    return contagem

def get_valores_reais_atividades(item_id):
    dados = qpre.pre_atividades_utilidade(item_id)

    # Mapeamento dos nomes longos para os curtos desejados
    legenda_curta = {
        "Parcialmente úteis - correção": "Correção incompleta",
        "Parcialmente úteis - desatualizadas": "Desatualizadas",
        "Muito úteis": "Muito úteis",
        "Parcialmente úteis - lacunas": "Lacunas de informação",
        "Não realizou": "Não realizou"
    }

    # Iniciar contagem com as novas categorias curtas
    contagem = {v: 0 for v in legenda_curta.values()}

    for _, _, categoria, total in dados:
        categoria_curta = legenda_curta.get(categoria, "Outro")
        if categoria_curta in contagem:
            contagem[categoria_curta] += total

    logger.debug(f"[DASHBOARD_PRE] Atividades (mapeado): {contagem}")
    return contagem


# =========================
# Layout principal
# =========================

def layout():

    return html.Div([

        html.Div(className="topo-dashboard", children=[
            html.Div(className="linha-superior", children=[
                html.Div(style={"marginLeft": "auto"}, children=[
                    dcc.Dropdown(id="dropdown_item", placeholder="Seleciona o e-Fólio", className="dashboard-pre-dropdown")
                ])
            ]),
            html.Div(id="barra_superior_formulario")
        ]),

        html.H2("Grau de Confiança Pré-Efólio", className="dashboard-pre-subsecao"),
        html.Div(id="info_total_respostas_pre"),
        
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
                dcc.Graph(id="grafico_confianca_preparacao", config={"displayModeBar": False}, style={"height": "180px"})
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Nº Horas de Preparação", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Mostra quantas horas os alunos dizem ter dedicado à preparação para o e-fólio.\n"
                        "As opções incluem:\n"
                        "- Menos de 5h\n"
                        "- 5 a 10h\n"
                        "- 10 a 20h\n"
                        "- 20 a 40h\n"
                        "- Mais de 40h",
                        className="tooltip-text"
                    )
                ]),
                dcc.Graph(id="grafico_horas_preparacao", config={"displayModeBar": False}, style={"height": "180px"})
            ])
        ]),

        html.Div("Qualidade dos recursos", className="dashboard-pre-subtitulo"),

        html.Div(className="dashboard-pre-row", children=[
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Acessibilidade", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Refere-se à facilidade com que os alunos conseguiram aceder e navegar pelos recursos da UC.\n"
                        "As categorias incluem:\n"
                        "- Acessíveis e bem organizados\n"
                        "- Acessíveis, mas estrutura confusa\n"
                        "- Pouco acessíveis e desorganizados",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_acessibilidade")
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Assertividade", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Mostra a perceção dos alunos sobre a utilidade dos recursos disponibilizados.\n"
                        "As categorias incluem:\n"
                        "- Muito úteis\n"
                        "- Parcialmente úteis - lacunas\n"
                        "- Pouco úteis - Necessitam revisão\n"
                        "- Não utilizados",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_assertividade")
            ]),
            html.Div(className="dashboard-pre-card", children=[
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Atividades Formativas", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Mostra a utilidade percebida das atividades formativas realizadas antes do e-fólio.\n"
                        "As categorias incluem:\n"
                        "- Muito úteis\n"
                        "- Correção incompleta\n"
						"- Desatualizadas\n"
						"- Lacunas de informação\n"
                        "- Não realizou",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_atividades")
            ]),
            html.Div(className="dashboard-pre-card", children=[  # Sessão Síncrona
                html.Div(className="tooltip-bloco", children=[
                    html.H4("Sessão Síncrona", className="tooltip-hover dashboard-pre-card-title"),
                    html.Span(
                        "Mostra a perceção dos alunos quanto à utilidade da sessão síncrona anterior ao e-fólio.\n"
                        "As categorias incluem:\n"
                        "- Muito útil\n"
                        "- Útil, mas com lacunas\n"
                        "- Não foi útil\n"
                        "- Ainda não se realizou",
                        className="tooltip-text"
                    )
                ]),
                html.Div(id="grafico_sessao_sincrona_pre")
            ])
        ])
    ])

# =========================
# Componentes visuais
# =========================

def render_grafico_confianca_pre(item_id):
    dados = qpre.pre_confianca_preparacao(item_id)

    df = pd.DataFrame(dados, columns=["item_id", "item_name", "categoria_preparacao", "total_respostas"])

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

def render_grafico_horas_preparacao(valores_dict):
    categorias = ["< 5h", "5 a 10h", "10 a 20h", "20 a 40h", "> 40h"]
    cores = ["#f7c59f", "#f9e79f", "#dcdcdc", "#aed6f1", "#76d7c4"]
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

def render_grafico_acessibilidade(valores_dict):
    categorias = [
        "Acessíveis e bem organizados",
        "Acessíveis, mas estrutura confusa",
        "Pouco acessíveis e desorganizados"
    ]
    cores = ["#90ee90", "#ffd700", "#f08080"]

    # Filtrar tudo baseado nos índices das categorias com valor > 0
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

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px", "minHeight": "300px"}, children=[
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

    # Filtrar tudo baseado nos índices das categorias com valor > 0
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

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px", "minHeight": "300px"}, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        legenda
    ])

def render_grafico_atividades(valores_dict):
    categorias = [
        "Correção imcompleta",
        "Desatualizadas",
        "Muito úteis",
        "Lacunas de informação",
        "Não realizou"
    ]
    cores = ["#f7c59f", "#ffeb99", "#90ee90", "#ff9999", "#d3d3d3"]

    # Filtrar tudo baseado nos índices das categorias com valor > 0
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

    return html.Div(style={"backgroundColor": "#f4faf4", "padding": "8px 12px", "minHeight": "300px"}, children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        legenda
    ])

def render_grafico_sessao_sincrona_pre(valores_dict):
    categorias = [
        "Muito útil",
        "Útil, mas com lacunas",
        "Não foi útil",
        "Ainda não se realizou"
    ]
    cores = ["#90ee90", "#ffd700", "#f08080", "#d3d3d3"]
    valores = [valores_dict.get(cat, 0) for cat in categorias]

    # Verifica se há dados
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
            height=200
        )
        return fig

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

def render_barra_uc_form(item_id):
    logger.debug(f"[DASHBOARD_PRE] Renderizando barra UC para item_id: {item_id}")
    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, course_name
        FROM efolios
        WHERE item_id = ?
        LIMIT 1
    """, (item_id,))
    resultado = cursor.fetchone()
    conn.close()

    logger.debug(f"[DASHBOARD_PRE] Resultado da consulta: {resultado}")
    if not resultado:
        logger.warning(f"[DASHBOARD_PRE] Nenhum e-fólio encontrado para item_id: {item_id}")
        return None

    nome_efolio, nome_curso = resultado
    texto_esquerda = f"{nome_curso} - {nome_efolio}"
    texto_direita = extrair_ano_letivo(nome_curso)

    return html.Div(className="barra-uc", children=[
        html.Span(texto_esquerda, className="nome-curso"),
        html.Span(texto_direita, className="ano-letivo")
    ])
