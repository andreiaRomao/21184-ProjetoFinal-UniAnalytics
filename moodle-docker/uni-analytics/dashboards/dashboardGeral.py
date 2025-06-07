from dash import html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import queries.queriesGeral as qg
import traceback
import re

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
# Função auxiliar: Info topo do dashboard
# =========================

def get_dashboard_top_info(userid, course_id):
    try:
        forum_data = qg.fetch_all_forum_posts()
        cursos = qg.fetch_user_course_data()

        utilizador = next((x for x in forum_data if x['userid'] == userid and x['course_id'] == course_id), None)
        curso = cursos[cursos['curso'].notna() & (cursos['curso'].str.contains(str(course_id)))].head(1)
        nome_curso = curso['curso'].values[0] if not curso.empty else f"{course_id} - UC Desconhecida"

        if utilizador:
            nome = f"{utilizador['firstname']} {utilizador['lastname']}"
            papel_raw = utilizador['role'].lower()
            papel = "ALUNO" if "student" in papel_raw else "PROFESSOR"
        else:
            nome = "Utilizador Desconhecido"
            papel = "-"

        return nome, papel, nome_curso

    except Exception as e:
        print("[ERRO] (get_dashboard_top_info):", e)
        return "Erro", "Erro", "Erro"

# =========================
# Obter cursos disponíveis para dropdown
# =========================

def obter_opcoes_dropdown_cursos():
    try:
        cursos = qg.fetch_user_course_data()
        cursos_validos = cursos[cursos['curso'].notna()]

        opcoes = []

        for _, linha in cursos_validos.iterrows():
            nome = linha['curso']
            match = re.match(r'^(\d+)\s*-\s*(.*)', nome)

            if match:
                # Curso começa por número → usa esse número como valor
                course_id = int(match.group(1))
                label = nome
                opcoes.append({
                    "label": label,
                    "value": course_id
                })
            else:
                # Curso sem ID → ignora ou trata separadamente
                # print(f"[IGNORADO] Curso sem ID numérico: {nome}")
                # Opcional: adicionar ao dropdown com o nome como valor?
                opcoes.append({"label": nome, "value": nome})
        return opcoes

    except Exception as e:
        print("[ERRO] (obter_opcoes_dropdown_cursos):", e)
        return []

# =========================
# Layout principal
# =========================

def layout(userid, course_id):
    try:
        anos_disponiveis = sorted(dados_pie_por_ano.keys())
        ano_inicial = anos_disponiveis[-1] if anos_disponiveis else ""
        nome, papel, curso = get_dashboard_top_info(userid, course_id)
        dropdown_cursos = obter_opcoes_dropdown_cursos()

        return html.Div(className="dashboard-geral", children=[
            html.Div(className="topo-dashboard", children=[
                html.Div(className="linha-superior", children=[
                    html.Div(className="info-utilizador", children=[
                        html.Div(className="avatar-icon"),
                        html.Span(f"[{papel}] {nome}", className="nome-utilizador")
                    ]),
                    html.Div(className="dropdown-curso", children=[
                        dcc.Dropdown(
                            id="dropdown_uc",
                            options=dropdown_cursos,
                            value=course_id,
                            clearable=False,
                            className="dropdown-uc-selector"
                        )
                    ])
                ]),
                html.Div(className="barra-uc", children=[
                    html.Span(curso, className="nome-curso"),
                    html.Span(ano_inicial, className="ano-letivo")
                ])
            ]),

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
