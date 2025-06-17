from dash import html, dcc, Input, Output, State
from dash_iconify import DashIconify
import plotly.express as px
import pandas as pd
import queries.queriesComuns as qg
import traceback
import re

# =========================
# Funções auxiliares para normalização e extração de dados
# =========================

def normalizar_itemname(nome):
    if not isinstance(nome, str):
        return ""
    nome = nome.lower()
    nome = re.sub(r'[^a-z0-9]', '', nome)
    return nome

def extrair_ano_letivo(course_name):
    match = re.search(r'_(\d{2})', course_name)
    if match:
        sufixo = int(match.group(1))
        ano_inicio = 2000 + sufixo
        return f"{ano_inicio}/{ano_inicio + 1}"
    return None

def classificar_aluno(grupo, notas):
    a = notas.get('efolioa', 0)
    b = notas.get('efoliob', 0)
    global_ = notas.get('global')
    recurso = notas.get('recurso')
    exame = notas.get('exame')
    exame_rec = notas.get('examerecurso')
    soma = a + b

    if 'exame' in grupo.lower():
        if exame and exame >= 9.5:
            return "Exame"
        elif exame and exame < 9.5 and exame_rec and exame_rec >= 9.5:
            return "Exame Recurso"
        else:
            return "Reprovado"
    else:
        if soma >= 3.5:
            if global_ and global_ >= 5.5 and soma + global_ >= 9.5:
                return "Efolio Global"
            elif recurso and recurso >= 5.5 and soma + recurso >= 9.5:
                return "Efolio Recurso"
            else:
                return "Reprovado"
        else:
            return "Reprovado"
        
# =========================
# Calcular estatísticas por ano 
# =========================

def calcular_estatisticas_por_ano(completions, cursos):
    completions['itemname'] = completions['itemname'].apply(normalizar_itemname)
    cursos['ano_letivo'] = cursos['course_name'].apply(extrair_ano_letivo)

    df = completions.merge(
        cursos[['userid', 'courseid', 'course_name', 'ano_letivo']],
        left_on=['userid', 'course_id'],
        right_on=['userid', 'courseid'],
        how='left'
    )

    anos = sorted(df['ano_letivo'].dropna().unique())
    if len(anos) > 0:
        ano_atual = anos[-1]
        anos = [a for a in anos if a != ano_atual]

    pie_por_ano = {}
    linhas_por_ano = {}
    inscritos_por_ano = (
        cursos[cursos['role'] == 'student'][['userid', 'ano_letivo']]
        .drop_duplicates()
        .groupby('ano_letivo')['userid']
        .nunique()
        .to_dict()
    )

    for ano in anos:
        df_ano = df[df['ano_letivo'] == ano]
        situacoes = {}

        for uid, grupo in df_ano.groupby('userid'):
            notas = grupo.set_index('itemname')['finalgrade'].to_dict()

            # Vai buscar o groupname diretamente de 'cursos'
            grupo_nome = cursos[
                (cursos['userid'] == uid) & (cursos['courseid'] == grupo['course_id'].iloc[0])
            ]['groupname'].dropna().unique()

            grupo_nome = grupo_nome[0].lower() if len(grupo_nome) > 0 else "desconhecido"

            situacao = classificar_aluno(grupo_nome, notas)
            situacoes[uid] = situacao

        contagem = pd.Series(situacoes.values()).value_counts().to_dict()
        pie_por_ano[ano] = contagem

        aprovados = sum(contagem.get(k, 0) for k in ["Efolio Global", "Efolio Recurso", "Exame", "Exame Recurso"])
        reprovados = contagem.get("Reprovado", 0)
        linhas_por_ano[ano] = [aprovados, reprovados]

    return linhas_por_ano, pie_por_ano, inscritos_por_ano

# =========================
# Callback de atualização
# =========================

def register_callbacks(app):
    @app.callback(
        Output("grafico_linhas", "figure"),
        Output("grafico_pie", "figure"),
        Output("grafico_linhas_inscritos", "figure"),  # ← corrigido aqui
        Input("dropdown_ano", "value"),
        State("store_dados_grafico", "data")
    )
    def atualizar_graficos(ano, store_data):
        linhas = store_data.get("linhas", {})
        pie = store_data.get("pie", {})
        inscritos = store_data.get("inscritos", {})

        return (
            construir_figura_linhas(linhas, ano),
            construir_figura_pie(pie, ano),
            construir_figura_linhas_inscritos(inscritos, ano)
        )


# =========================
# Função auxiliar: Info topo do dashboard
# =========================

def get_dashboard_top_info(userid, course_id):
    try:
        cursos = qg.fetch_user_course_data()

        # Filtra apenas pelo utilizador e curso atual
        linha = cursos[(cursos['userid'] == userid) & (cursos['courseid'] == course_id)].head(1)

        if not linha.empty:
            nome = linha['name'].values[0]
            papel_raw = linha['role'].values[0].lower()
            papel = "ALUNO" if "student" in papel_raw else "PROFESSOR"
            nome_curso = linha['course_name'].values[0]
        else:
            nome = "Utilizador Desconhecido"
            papel = "-"
            nome_curso = f"{course_id} - UC Desconhecida"

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
        cursos_validos = cursos[cursos['course_name'].notna()]

        opcoes = []

        # Elimina cursos duplicados (caso o mesmo curso apareça para vários users)
        cursos_unicos = cursos_validos.drop_duplicates(subset=["course_name"])

        for _, linha in cursos_unicos.iterrows():
            nome = linha['course_name']
            opcoes.append({
                "label": nome,
                "value": nome
            })

        return opcoes

    except Exception as e:
        print("[ERRO] (obter_opcoes_dropdown_cursos):", e)
        return []


# =========================
# Layout principal
# =========================

def layout(userid, course_id):
    try:
        dados_completions = pd.DataFrame(qg.fetch_all_completions())
        dados_cursos = pd.DataFrame(qg.fetch_user_course_data())
        linhas_por_ano, pie_por_ano, inscritos_por_ano = calcular_estatisticas_por_ano(dados_completions, dados_cursos)

        store_data = {
            "linhas": linhas_por_ano,
            "pie": pie_por_ano,
            "inscritos": inscritos_por_ano
        }

        anos_disponiveis = sorted(pie_por_ano.keys())
        ano_inicial = anos_disponiveis[-1] if anos_disponiveis else ""

        nome, papel, curso = get_dashboard_top_info(userid, course_id)
        ano_curso_atual = extrair_ano_letivo(curso) or ""
        dropdown_cursos = obter_opcoes_dropdown_cursos()

        return html.Div(className="dashboard-geral", children=[
            dcc.Store(id="store_dados_grafico", data=store_data),

            html.Div(className="topo-dashboard", children=[
                html.Div(className="linha-superior", children=[
                    html.Div(className="info-utilizador", children=[
                        DashIconify(
                            icon="mdi:school" if papel == "ALUNO" else "mdi:teach",
                            width=32,
                            color="#2c3e50",
                            className="avatar-icon"
                        ),
                        html.Span(f"[{papel}] {nome}", className="nome-utilizador")
                    ]),
                    html.Div(className="dropdown-curso", children=[
                        dcc.Dropdown(
                            id="dropdown_uc",
                            options=dropdown_cursos,
                            value=course_id,
                            clearable=False,
                            className="dropdown-uc-selector dashboard-geral-oculto"  
                        )
                    ])
                ]),
                html.Div(className="barra-uc", children=[
                    html.Span(curso, className="nome-curso"),
                    html.Span(ano_curso_atual, className="ano-letivo")
                ])
            ]),

            html.H3("Informação Geral da Unidade Curricular", className="dashboard-geral-titulo"),

            html.Div(className="linha-flex", children=[
                html.Div(className="coluna-esquerda", children=[
                    html.Div(className="card bg-verde-suave", children=[
                        html.H4("Taxa de Aprovação/reprovação nos últimos 5 anos", className="card-section-title"),
                        dcc.Graph(
                            id="grafico_linhas",
                            figure=construir_figura_linhas(linhas_por_ano, ano_inicial),
                            config={"displayModeBar": False},
                            className="dashboard-geral-grafico"
                        )
                    ])
                ]),
                html.Div(className="coluna-direita", children=[
                    html.Div(className="card bg-verde-suave", children=[
                        html.Div(className="dashboard-geral-dropdown-barra", children=[
                            html.H4("Taxa de Aprovação por tipo de avaliação", className="card-section-title"),
                            dcc.Dropdown(
                                id="dropdown_ano",
                                options=[{"label": ano, "value": ano} for ano in pie_por_ano.keys()],
                                value=ano_inicial,
                                clearable=False,
                                className="dropdown-uc-selector"
                            )
                        ]),
                        dcc.Graph(
                            id="grafico_pie",
                            figure=construir_figura_pie(pie_por_ano, ano_inicial),
                            config={"displayModeBar": False},
                            className="dashboard-geral-grafico"
                        )
                    ])
                ])
            ]),

            html.Div(className="dashboard-geral-grafico-inscritos-wrapper", children=[
                html.Div(className="card bg-verde-suave", children=[
                    html.H4("Evolução do número de inscritos por ano letivo", className="card-section-title"),
                    dcc.Graph(
                        id="grafico_linhas_inscritos",
                        figure=construir_figura_linhas_inscritos(inscritos_por_ano, ano_inicial),
                        config={"displayModeBar": False},
                        className="dashboard-geral-grafico"
                    )
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

def construir_figura_linhas(linhas_por_ano, ano_selecionado):
    ano_final = int(ano_selecionado.split("/")[0])
    anos_eixo = list(range(ano_final - 4, ano_final + 1))

    df = pd.DataFrame(columns=["Ano", "Situação", "Total"])
    anos_formatados = []  

    for ano in anos_eixo:
        str_ano = f"{ano}/{ano+1}"
        aprov, repro = linhas_por_ano.get(str_ano, [0, 0])
        df = pd.concat([
            df,
            pd.DataFrame({
                "Ano": [str_ano, str_ano],
                "Situação": ["Aprovados", "Reprovados"],
                "Total": [aprov, repro]
            })
        ])
        anos_formatados.append(str_ano)

    fig = px.line(df, x="Ano", y="Total", color="Situação", markers=True,
                  category_orders={"Ano": anos_formatados},
                  color_discrete_map={"Aprovados": "#80cfa9", "Reprovados": "#5bb0f6"},
                  height=280)

    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=20, b=30),
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50"),
        showlegend=True,
        xaxis=dict(tickmode="array", tickvals=anos_formatados)
    )
    return fig

def construir_figura_pie(pie_por_ano, ano):
    dados = pie_por_ano.get(ano, {})

    ordem = ["Efolio Global", "Efolio Recurso", "Exame", "Exame Recurso"]
    dados_ordenados = {k: dados[k] for k in ordem if k in dados}

    df = pd.DataFrame({
        "Tipo": list(dados_ordenados.keys()),
        "Percentagem": list(dados_ordenados.values())
    })

    fig = px.pie(df, names="Tipo", values="Percentagem", hole=0.45,
                 color_discrete_sequence=["#94e0e4", "#69b3dd", "#386c95", "#ffc658", "#f08080"],
                 category_orders={"Tipo": ordem}, height=280)
    fig.update_traces(textinfo="label+percent", textfont_size=9)
    fig.update_layout(
        height=220,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.6,
            xanchor="center",
            x=-10,
            font=dict(size=13),
            itemwidth=40,
            tracegroupgap=0
        )
    )
    return fig

def construir_figura_linhas_inscritos(dados_inscritos, ano_base):
    ano_final = int(ano_base.split("/")[0])
    anos_eixo = list(range(ano_final - 4, ano_final + 1))
    anos_letivos = [f"{ano}/{ano + 1}" for ano in anos_eixo]

    totais = [dados_inscritos.get(ano, 0) for ano in anos_letivos]
    df = pd.DataFrame({
        "Ano": anos_letivos,
        "Inscritos": totais
    })

    fig = px.line(df, x="Ano", y="Inscritos", markers=True,
                  category_orders={"Ano": anos_letivos},
                  color_discrete_sequence=["#f4b642"],
                  height=280)

    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=20, b=30),
        paper_bgcolor="#f4faf4",
        plot_bgcolor="#f4faf4",
        font=dict(color="#2c3e50"),
        showlegend=False,
        xaxis=dict(tickmode="array", tickvals=anos_letivos)
    )
    return fig