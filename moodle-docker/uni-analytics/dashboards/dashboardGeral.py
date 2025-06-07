from dash import html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import traceback

# =========================
# DADOS MARTELADOS POR ANO
# =========================

dados_linhas_por_ano = {
    '2020/2021': [230, 140],
    '2021/2022': [180, 120],
    '2022/2023': [410, 200],
    '2023/2024': [320, 90],
}

dados_pie_por_ano = {
    '2020/2021': {'Global': 50.0, 'Exame': 30.0, 'Recurso': 20.0},
    '2021/2022': {'Global': 60.0, 'Exame': 25.0, 'Recurso': 15.0},
    '2022/2023': {'Global': 58.0, 'Exame': 22.0, 'Recurso': 20.0},
    '2023/2024': {'Global': 62.5, 'Exame': 12.5, 'Recurso': 25.0}
}

# =========================
# Callback de atualização
# =========================

def register_callbacks(app):
    @app.callback(
        Output("grafico_linhas", "figure"),
        Output("grafico_pie", "figure"),
        Input("dropdown_ano", "value")
    )
    def atualizar_graficos(ano):
        return construir_figura_linhas(ano), construir_figura_pie(ano)

# =========================
# Layout principal
# =========================

def layout():
    try:
        ano_inicial = "2023/2024"

        return html.Div(className="dashboard-geral", children=[
            html.H3("Dashboard Geral de Unidade Curricular", style={"textAlign": "center"}),

            html.Div(className="linha-flex", children=[
                html.Div(className="coluna-esquerda", children=[
                    html.Div(className="card bg-verde-suave", children=[
                        html.Div(style={
                            "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                            "minHeight": "36px"
                        }, children=[
                            html.H4("Taxa de Aprovação/reprovação nos últimos 5 anos",
                                    className="card-section-title", style={"textAlign": "center", "width": "100%"}),
                            html.Div()
                        ]),
                        html.Div(style={"display": "flex", "justifyContent": "center", "alignItems": "center", "flex": "1"},
                                 children=[
                                     dcc.Graph(
                                         id="grafico_linhas",
                                         figure=construir_figura_linhas(ano_inicial),
                                         config={"displayModeBar": False},
                                         style={"height": "300px", "width": "100%"}
                                     )
                                 ])
                    ])
                ]),
                html.Div(className="coluna-direita", children=[
                    html.Div(className="card bg-verde-suave", children=[
                        html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                                        "minHeight": "36px"}, children=[
                            html.H4("Taxa de Aprovação por tipo de avaliação", className="card-section-title"),
                            dcc.Dropdown(
                                id="dropdown_ano",
                                options=[{"label": ano, "value": ano} for ano in dados_pie_por_ano.keys()],
                                value=ano_inicial,
                                clearable=False,
                                style={"width": "130px", "fontSize": "13px", "marginTop": "0px"}
                            )
                        ]),
                        html.Div(style={"display": "flex", "flexDirection": "column", "alignItems": "center", "flex": "1"},
                                 children=[
                                     dcc.Graph(
                                         id="grafico_pie",
                                         figure=construir_figura_pie(ano_inicial),
                                         config={"displayModeBar": False},
                                         style={"height": "300px", "width": "100%"}
                                     )
                                 ])
                    ])
                ])
            ])
        ])
    except Exception as e:
        print("[ERRO] (layout) Falha ao gerar o dashboard geral.")
        traceback.print_exc()
        return html.Div("Erro ao carregar o dashboard geral.")

# =========================
# Funções de construção de gráficos
# =========================

def construir_figura_linhas(ano_selecionado):
    # Extrai o ano base (ex: "2022/2023" → 2022)
    ano_final = int(ano_selecionado.split("/")[0])

    # Gera os últimos 5 anos
    anos_eixo = list(range(ano_final - 4, ano_final + 1))

    # Recolhe os dados disponíveis (se existirem no dicionário)
    dados = {
        ano: dados_linhas_por_ano[ano]
        for ano in dados_linhas_por_ano
        if int(ano.split("/")[0]) in anos_eixo
    }

    df = pd.DataFrame({
        "Ano": [],
        "Situação": [],
        "Total": []
    })

    for ano in anos_eixo:
        str_ano = f"{ano}/{ano+1}"
        if str_ano in dados:
            aprov, repro = dados[str_ano]
            df = pd.concat([
                df,
                pd.DataFrame({
                    "Ano": [ano, ano],
                    "Situação": ["Aprovados", "Reprovados"],
                    "Total": [aprov, repro]
                })
            ])
        else:
            # ano sem dados → ignora no gráfico, mas ano estará no eixo
            continue

    # Força presença dos anos no eixo X, mesmo sem dados
    fig = px.line(df, x="Ano", y="Total", color="Situação", markers=True,
                  category_orders={"Ano": anos_eixo},
                  color_discrete_map={"Aprovados": "#80cfa9", "Reprovados": "#5bb0f6"},
                  height=280)

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=30),
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50"),
        showlegend=True,
        xaxis=dict(tickmode="array", tickvals=anos_eixo)
    )
    return fig




def construir_figura_pie(ano):
    dados = dados_pie_por_ano[ano]
    df = pd.DataFrame({
        "Tipo": list(dados.keys()),
        "Percentagem": list(dados.values())
    })

    fig = px.pie(df, names="Tipo", values="Percentagem", hole=0.45,
                 color_discrete_sequence=["#94e0e4", "#69b3dd", "#386c95"], height=280)
    fig.update_traces(textinfo="label+percent")
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    return fig
