from dash import html, dcc, Input, Output, State
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import queries.queriesComuns as qg
import traceback
import re
from utils.logger import logger
import unicodedata

# =========================
# Funções auxiliares para normalização e extração de dados
# =========================

def normalizar_itemname(nome):
    if not isinstance(nome, str):
        logger.warning(f"[NORMALIZAR] Nome inválido (não string): {nome}")
        return ""
    
    nome_original = nome
    # Remove acentuação
    nome = unicodedata.normalize("NFKD", nome).encode("ASCII", "ignore").decode("utf-8")
    nome = nome.lower()
    nome = re.sub(r'[^a-z0-9]', '', nome)
    
    logger.debug(f"[NORMALIZAR] '{nome_original}' normalizado para '{nome}'")
    return nome

def extrair_ano_letivo(course_name):
    match = re.search(r'_(\d{2})', course_name)
    if match:
        sufixo = int(match.group(1))
        ano_inicio = 2000 + sufixo
        ano_letivo = f"{ano_inicio}/{ano_inicio + 1}"
        logger.debug(f"[ANO] Ano letivo extraído de '{course_name}': {ano_letivo}")
        return ano_letivo
    logger.warning(f"[ANO] Falha ao extrair ano letivo de: {course_name}")
    return None

def classificar_aluno(grupo, notas):
    a = notas.get('efolioa', 0)
    b = notas.get('efoliob', 0)
    global_ = notas.get('global')
    recurso = notas.get('recurso')
    exame = notas.get('exame')
    exame_rec = notas.get('examerecurso')
    soma = a + b

    logger.debug(f"[CLASSIFICAR] Grupo: {grupo} | Notas: {notas}")

    if 'exame' in grupo.lower():
        if exame and exame >= 9.5:
            logger.info(f"[CLASSIFICAR] Classificação final: Exame")
            return "Exame"
        elif exame and exame < 9.5 and exame_rec and exame_rec >= 9.5:
            logger.info(f"[CLASSIFICAR] Classificação final: Exame Recurso")
            return "Exame Recurso"
        else:
            logger.info(f"[CLASSIFICAR] Classificação final: Reprovado (Exame)")
            return "Reprovado"
    else:
        if soma >= 3.5:
            if global_ and global_ >= 5.5 and soma + global_ >= 9.5:
                logger.info(f"[CLASSIFICAR] Classificação final: Efolio Global")
                return "Efolio Global"
            elif recurso and recurso >= 5.5 and soma + recurso >= 9.5:
                logger.info(f"[CLASSIFICAR] Classificação final: Efolio Recurso")
                return "Efolio Recurso"
            else:
                logger.info(f"[CLASSIFICAR] Classificação final: Reprovado (E-fólios)")
                return "Reprovado"
        else:
            logger.info(f"[CLASSIFICAR] Classificação final: Reprovado (nota insuficiente)")
            return "Reprovado"
        
# =========================
# Calcular estatísticas por ano 
# =========================

def calcular_estatisticas_por_ano(completions, cursos):
    logger.debug("Início do cálculo de estatísticas por ano.")

    completions['item_name'] = completions['item_name'].apply(normalizar_itemname)
    cursos['ano_letivo'] = cursos['course_name'].apply(extrair_ano_letivo)

    logger.debug("Dados normalizados e ano letivo extraído dos nomes dos cursos.")

    df = completions.merge(
        cursos[['user_id', 'course_id', 'course_name', 'ano_letivo']],
        left_on=['user_id', 'course_id'],
        right_on=['user_id', 'course_id'],
        how='left'
    )

    anos = sorted(df['ano_letivo'].dropna().unique())
    if len(anos) > 0:
        ano_atual = anos[-1]
        anos = [a for a in anos if a != ano_atual]

    logger.info(f"Anos letivos a analisar (excluindo o atual '{ano_atual}'): {anos}")

    pie_por_ano = {}
    linhas_por_ano = {}
    inscritos_por_ano = (
        cursos[cursos['role'] == 'student'][['user_id', 'ano_letivo']]
        .drop_duplicates()
        .groupby('ano_letivo')['user_id']
        .nunique()
        .to_dict()
    )

    logger.debug(f"Número de inscritos por ano: {inscritos_por_ano}")

    for ano in anos:
        df_ano = df[df['ano_letivo'] == ano]
        situacoes = {}

        for uid, grupo in df_ano.groupby('user_id'):
            notas = grupo.set_index('item_name')['final_grade'].to_dict()
            grupo_nome = cursos[
                (cursos['user_id'] == uid) & (cursos['course_id'] == grupo['course_id'].iloc[0])
            ]['group_name'].dropna().unique()
            grupo_nome = grupo_nome[0].lower() if len(grupo_nome) > 0 else "desconhecido"

            situacao = classificar_aluno(grupo_nome, notas)
            situacoes[uid] = situacao

        contagem = pd.Series(situacoes.values()).value_counts().to_dict()
        pie_por_ano[ano] = contagem

        aprovados = sum(contagem.get(k, 0) for k in ["Efolio Global", "Efolio Recurso", "Exame", "Exame Recurso"])
        reprovados = contagem.get("Reprovado", 0)
        linhas_por_ano[ano] = [aprovados, reprovados]

        logger.info(f"Ano {ano}: {aprovados} aprovados, {reprovados} reprovados | Distribuição: {contagem}")

    logger.debug("Estatísticas por ano calculadas com sucesso.")
    return linhas_por_ano, pie_por_ano, inscritos_por_ano

# =========================
# Callback de atualização
# =========================

def register_callbacks(app):
    @app.callback(
        Output("grafico_linhas", "figure"),
        Output("grafico_pie", "figure"),
        Output("grafico_linhas_inscritos", "figure"), 
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

    @app.callback(
        Output("info_nome_utilizador", "children"),
        Output("info_nome_curso", "children"),
        Input("dropdown_uc", "value"),
        State("store_user_id", "data")
    )
    def atualizar_topo_info(novo_course_id, user_id):
        nome, papel, nome_curso = get_dashboard_top_info(user_id, novo_course_id)
        logger.debug(f"[TOPO_INFO] Atualizado: {nome} [{papel}] - {nome_curso}")
        return f"[{papel}] {nome}", nome_curso

    @app.callback(
        Output("store_dados_grafico", "data"),
        Input("dropdown_uc", "value"),
        State("store_user_id", "data")
    )
    def atualizar_dados_grafico(course_id, user_id):
        try:
            # Obtemos todos os dados
            completions = pd.DataFrame(qg.fetch_all_grade_progress_local())
            cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())

            # Encontrar o nome do curso atual para extrair a uc_id
            nome_curso = cursos.loc[
                (cursos['user_id'] == user_id) & (cursos['course_id'] == course_id),
                'course_name'
            ].values

            if len(nome_curso) == 0:
                logger.warning(f"[STORE_DADOS] Curso {course_id} não encontrado para o utilizador {user_id}")
                return {}

            uc_id = re.search(r'(\d{5})', nome_curso[0])
            if not uc_id:
                logger.warning(f"[STORE_DADOS] uc_id não extraído de '{nome_curso[0]}'")
                return {}

            uc_id = uc_id.group(1)

            # Filtrar cursos e completions pela mesma uc_id
            cursos['uc_id'] = cursos['course_name'].str.extract(r'(\d{5})')
            cursos_filtrados = cursos[cursos['uc_id'] == uc_id]
            completions_filtrados = completions[completions['course_id'].isin(cursos_filtrados['course_id'])]

            # Recalcular estatísticas
            linhas_por_ano, pie_por_ano, inscritos_por_ano = calcular_estatisticas_por_ano(
                completions_filtrados, cursos_filtrados
            )

            return {
                "linhas": linhas_por_ano,
                "pie": pie_por_ano,
                "inscritos": inscritos_por_ano
            }

        except Exception as e:
            logger.exception("[ERRO] (atualizar_dados_grafico): Erro ao atualizar dados do gráfico")
            return {}

    @app.callback(
        Output("dropdown_ano", "value"),
        Input("store_dados_grafico", "data")
    )
    def atualizar_dropdown_ano(store_data):
        try:
            anos = list(store_data.get("pie", {}).keys())
            if not anos:
                return None
            return sorted(anos)[-1]  # Último ano disponível
        except Exception as e:
            logger.exception("[DASHBOARD] Erro ao atualizar dropdown_ano")
            return None

# =========================
# Função auxiliar: Info topo do dashboard
# =========================

def get_dashboard_top_info(user_id, course_id):
    try:
        cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())  # Dados dos cursos locais

        linha = cursos[(cursos['user_id'] == user_id) & (cursos['course_id'] == course_id)].head(1)

        if not linha.empty:
            nome = linha['name'].values[0]
            papel_raw = linha['role'].values[0].lower()
            papel = "ALUNO" if "student" in papel_raw else "PROFESSOR"
            nome_curso = linha['course_name'].values[0]
            logger.debug(f"[DASHBOARD_INFO] Utilizador {user_id} no curso {course_id}: {nome} ({papel}) - {nome_curso}")
        else:
            nome = "Utilizador Desconhecido"
            papel = "-"
            nome_curso = f"{course_id} - UC Desconhecida"
            logger.warning(f"[DASHBOARD_INFO] Nenhum dado encontrado para user_id={user_id}, course_id={course_id}")

        return nome, papel, nome_curso

    except Exception as e:
        logger.exception(f"[ERRO] (get_dashboard_top_info): {e}")
        return "Erro", "Erro", "Erro"

# =========================
# Obter cursos disponíveis para dropdown
# =========================

def obter_opcoes_dropdown_cursos(user_id):
    try:
        cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())
        cursos_user = cursos[cursos['user_id'] == user_id]
        logger.debug(f"[Dropdown] Cursos do utilizador {user_id}: {cursos_user[['course_id', 'course_name']].to_dict(orient='records')}")

        cursos_validos = cursos_user[cursos_user['course_name'].notna()].copy()
        cursos_validos['uc_id'] = cursos_validos['course_name'].str.extract(r'(\d{5})')
        logger.debug(f"[Dropdown] Cursos com uc_id extraído: {cursos_validos[['course_id', 'course_name', 'uc_id']].to_dict(orient='records')}")

        cursos_ordenados = cursos_validos.sort_values(by="course_name", ascending=False)
        cursos_unicos = cursos_ordenados.drop_duplicates(subset=["uc_id"])

        opcoes = [
            {"label": linha['course_name'], "value": linha['course_id']}
            for _, linha in cursos_unicos.iterrows()
        ]
        logger.debug(f"[Dropdown] Opções finais para dropdown (user_id={user_id}): {opcoes}")

        return opcoes

    except Exception as e:
        logger.error("[ERRO] (obter_opcoes_dropdown_cursos):", exc_info=True)
        return []
    
# =========================
# Layout principal
# =========================

def layout(user_id):
    try:
        dados_completions = pd.DataFrame(qg.fetch_all_grade_progress_local())
        dados_cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())
        
        dropdown_cursos = obter_opcoes_dropdown_cursos(user_id)
        course_id_inicial = dropdown_cursos[0]['value'] if dropdown_cursos else None
        
        linhas_por_ano, pie_por_ano, inscritos_por_ano = calcular_estatisticas_por_ano(dados_completions, dados_cursos)

        store_data = {
            "linhas": linhas_por_ano,
            "pie": pie_por_ano,
            "inscritos": inscritos_por_ano
        }

        anos_disponiveis = sorted(pie_por_ano.keys())
        ano_inicial = anos_disponiveis[-1] if anos_disponiveis else ""

        nome, papel, curso = get_dashboard_top_info(user_id, course_id_inicial)
        ano_curso_atual = extrair_ano_letivo(curso) or ""
        dropdown_cursos = obter_opcoes_dropdown_cursos(user_id)

        return html.Div(className="dashboard-geral", children=[
            dcc.Store(id="store_dados_grafico", data=store_data),
            dcc.Store(id="store_user_id", data=user_id),

            html.Div(className="topo-dashboard", children=[
                html.Div(className="linha-superior", children=[
                    html.Div(className="info-utilizador", children=[
                        DashIconify(
                            icon="mdi:school" if papel == "ALUNO" else "mdi:teach",
                            width=32,
                            color="#2c3e50",
                            className="avatar-icon"
                        ),
                        html.Span(f"[{papel}] {nome}", className="nome-utilizador", id="info_nome_utilizador")
                    ]),
                    html.Div(className="dropdown-curso", children=[
                        dcc.Dropdown(
                            id="dropdown_uc",
                            options=dropdown_cursos,
                            value=course_id_inicial,
                            clearable=False,
                            className="dropdown-uc-selector" 
                        )
                    ])
                ]),
                html.Div(className="barra-uc", children=[
                    html.Span(id="info_nome_curso", className="nome-curso"),
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

    # Verifica se não há dados válidos
    if not dados_ordenados or sum(dados_ordenados.values()) == 0:
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
            margin=dict(t=20, b=20, l=20, r=20),
            height=220
        )
        return fig

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