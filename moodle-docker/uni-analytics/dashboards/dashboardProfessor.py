from dash import html, dcc, Input, Output, State
from dash_iconify import DashIconify
import queries.queriesProfessor as qp
import queries.queriesComuns as qg
import plotly.graph_objects as go
import plotly.express as px
import traceback
import pandas as pd
import re
import unicodedata
from datetime import datetime
from collections import defaultdict 
from utils.logger import logger

import warnings
warnings.simplefilter("always", pd.errors.SettingWithCopyWarning)
pd.options.mode.chained_assignment = "warn"

# =========================
# Funções de lógica modular
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

def alunos_inscritos_uc(cursos, course_id):
    logger.debug("alunos_inscritos_uc: filtrando cursos para course_id=%s", course_id)
    cursos_df = pd.DataFrame(cursos)
    return cursos_df[
        (cursos_df['course_id'] == course_id) &
        (cursos_df['role'] == 'student')
    ]['user_id'].unique()

def filtrar_alunos_avaliacao_continua(cursos, course_id):
    logger.debug("filtrar_alunos_avaliacao_continua: course_id=%s", course_id)
    cursos_df = pd.DataFrame(cursos)
    estudantes = cursos_df[
        (cursos_df['course_id'] == course_id) &
        (cursos_df['role'] == 'student')
    ].copy()
    estudantes['grupo'] = estudantes['group_name'].fillna('').str.lower()
    return estudantes[estudantes['grupo'].str.contains('aval')]['user_id'].unique()

def contar_conteudos_publicados(dados, user_id, course_id):
    logger.debug("contar_conteudos_publicados: professor %s, course_id %s", user_id, course_id)
    tipos = {
        'resource': 'Ficheiros', 'page': 'Páginas', 'url': 'Links',
        'book': 'Livros', 'folder': 'Pastas', 'quiz': 'Quizzes', 'lesson': 'Lições', 'forum': 'Fóruns' , 'scorm': 'Conteudos Publicados'
    }
    contagem = {nome: 0 for nome in tipos.values()}
    for d in dados:
        if d['course_id'] == course_id:
            tipo_raw = d.get('module_type')
            if tipo_raw in tipos:
                contagem[tipos[tipo_raw]] += 1
    logger.debug("contagem de conteúdos publicada: %r", contagem)
    return contagem

def contar_topicos_respostas_professor(dados, user_id, course_id):
    logger.debug("contar_topicos_respostas_professor: professor %s, course_id %s", user_id, course_id)
    criados = sum(1 for d in dados if d['user_id'] == user_id and d['course_id'] == course_id and d['post_type'] == 'topic')
    respondidos = sum(1 for d in dados if d['user_id'] == user_id and d['course_id'] == course_id and d['post_type'] == 'reply')
    logger.debug("tópicos criados=%d, respondidos=%d", criados, respondidos)
    return criados, respondidos

def calcular_velocidade_resposta(posts, user_id, course_id):
    logger.debug("calcular_velocidade_resposta: professor %s, course_id %s", user_id, course_id)
    posts_curso = [p for p in posts if p["course_id"] == course_id]
    posts_aluno = [p for p in posts_curso if "student" in (p.get("role") or "").lower()]
    tempos_resposta = []
    for post_aluno in posts_aluno:
        tempo_post = datetime.fromtimestamp(post_aluno["time_created"])
        respostas_professor = [p for p in posts_curso if p.get("parent") == post_aluno["post_id"] and p["user_id"] == user_id]
        if respostas_professor:
            tempo_resposta = datetime.fromtimestamp(min(respostas_professor, key=lambda p: p["time_created"])["time_created"])
            delta = (tempo_resposta - tempo_post).total_seconds() / (3600 * 24)
            tempos_resposta.append(delta)
    if tempos_resposta:
        media = sum(tempos_resposta) / len(tempos_resposta)
        dias = int(media); horas = round((media - dias) * 24)
        resultado = f"{dias} dia{'s' if dias != 1 else ''} e {horas} horas"
        logger.debug("velocidade de resposta calculada: %s", resultado)
        return resultado
    logger.debug("nenhuma resposta encontrada para cálculo de velocidade")
    return None

def calcular_media_acessos_semanal(acessos, user_id, course_id):
    logger.debug("calcular_media_acessos_semanal: professor %s, course_id %s", user_id, course_id)
    acessos_prof = [a for a in acessos if a["user_id"] == user_id and a["course_id"] == course_id]
    semanas = defaultdict(int)
    for a in acessos_prof:
        dt = a["access_time"]
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        semanas[dt.strftime("%Y-%W")] += 1
    media = round(sum(semanas.values()) / len(semanas), 1) if semanas else 0
    logger.debug("média semanal de acessos: %s", media)
    return media

def calcular_distribuicao_desempenho_global_professor(completions, cursos, course_id):
    logger.debug("calcular_distribuicao_desempenho_global_professor: course_id %s", course_id)
    completions_df = pd.DataFrame(completions)
    cursos_df = pd.DataFrame(cursos)
    distribuicao = {"Crítico": 0, "Em Risco": 0, "Expectável": 0}
    estudantes = cursos_df[(cursos_df['course_id'] == course_id) & (cursos_df['role'] == 'student')].copy()
    estudantes['grupo'] = estudantes['group_name'].fillna('').str.lower()
    alunos_ids = estudantes[estudantes['grupo'].str.contains('aval')]['user_id'].unique()
    for aluno_id in alunos_ids:
        soma = 0.0
        notas_aluno = completions_df[
            (completions_df['user_id']==aluno_id)&(completions_df['course_id']==course_id)&(completions_df['module_type']=='assign')]
        for _, l in notas_aluno.iterrows():
            nome_item = normalizar_itemname(l.get("item_name") or "")
            if "efolio" in nome_item:
                try: soma += float(l["final_grade"])
                except: continue
        categoria = "Crítico" if soma < 3.5 else "Em Risco" if soma < 4.5 else "Expectável"
        distribuicao[categoria] += 1
    logger.debug("distribuição de desempenho: %r", distribuicao)
    return distribuicao

def get_dashboard_top_info(user_id, course_id):
    logger.debug("get_dashboard_top_info: user %s, course_id %s", user_id, course_id)
    try:
        cursos = qg.fetch_all_user_course_data_local()
        df = pd.DataFrame(cursos)
        linha = df[(df['user_id'] == user_id) & (df['course_id'] == course_id)].head(1)
        if not linha.empty:
            nome = linha['name'].values[0]
            papel = "ALUNO" if "student" in linha['role'].values[0].lower() else "PROFESSOR"
            nome_curso = linha['course_name'].values[0]
        else:
            nome, papel, nome_curso = "Utilizador Desconhecido", "-", f"{course_id} - UC Desconhecida"
        logger.debug("top info: nome=%s, papel=%s, curso=%s", nome, papel, nome_curso)
        return nome, papel, nome_curso
    except Exception as e:
        logger.error("erro em get_dashboard_top_info: %s", e, exc_info=True)
        return "Erro", "Erro", "Erro"

def extrair_ano_letivo(course_name):
    logger.debug("extrair_ano_letivo: course_name=%s", course_name)
    match = re.search(r'_(\d{2})', course_name)
    if match:
        ano_inicio = 2000 + int(match.group(1))
        resultado = f"{ano_inicio}/{ano_inicio+1}"
        logger.debug("ano letivo extraído: %s", resultado)
        return resultado
    logger.debug("ano letivo não encontrado em course_name")
    return None

def obter_ultimo_acesso_uc(acessos, user_id, course_id):
    logger.debug("obter_ultimo_acesso_uc: professor %s, course_id %s", user_id, course_id)
    acessos_prof = [a for a in acessos if a["user_id"] == user_id and a["course_id"] == course_id]
    if not acessos_prof:
        logger.debug("nenhum acesso encontrado")
        return "—"
    mais_recente = max(acessos_prof, key=lambda a: a["access_time"])
    dt = mais_recente["access_time"]
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    res = dt.strftime("%d/%m/%Y")
    logger.debug("último acesso: %s", res)
    return res

def calcular_medias_efolios(completions, cursos, course_id):
    logger.debug("calcular_medias_efolios: início para course_id=%s", course_id)
    completions_df = pd.DataFrame(completions)
    alunos_aval = filtrar_alunos_avaliacao_continua(cursos, course_id)

    notas_a, notas_b, notas_c = [], [], []

    for aluno_id in alunos_aval:
        notas_aluno = completions_df[
            (completions_df['user_id'] == aluno_id) &
            (completions_df['course_id'] == course_id) &
            (completions_df['module_type'] == 'assign')
        ]

        nota_a = nota_b = nota_c = 0.0

        for _, row in notas_aluno.iterrows():
            nome = normalizar_itemname(row.get("item_name"))
            nota = float(row.get("final_grade") or 0)

            if "efolioa" in nome.replace(" ", ""):
                nota_a = nota
            elif "efoliob" in nome.replace(" ", ""):
                nota_b = nota
            elif "efolioc" in nome.replace(" ", ""):
                nota_c = nota

        notas_a.append(nota_a)
        notas_b.append(nota_b)
        if nota_c > 0:
            notas_c.append(nota_c)

    def media(lista):
        return round(sum(lista) / len(lista), 1) if lista else 0.0

    resultado = {
        "E-fólio A": media(notas_a),
        "E-fólio B": media(notas_b),
    }

    if notas_c:
        resultado["E-fólio C"] = media(notas_c)

    resultado["Total"] = round(sum(resultado.values()), 1)
    logger.debug("calcular_medias_efolios: resultado=%r", resultado)
    return resultado

def calcular_taxa_conclusao_efolios(completions, cursos, course_id):
    logger.debug("calcular_taxa_conclusao_efolios: início para course_id=%s", course_id)
    completions_df = pd.DataFrame(completions)
    alunos_aval = filtrar_alunos_avaliacao_continua(cursos, course_id)

    estado_a, estado_b, estado_c = [], [], []

    for aluno_id in alunos_aval:
        notas_aluno = completions_df[
            (completions_df["user_id"] == aluno_id) &
            (completions_df["course_id"] == course_id) &
            (completions_df["module_type"] == "assign")
        ]

        estado_aluno_a = estado_aluno_b = estado_aluno_c = 0

        for _, row in notas_aluno.iterrows():
            nome = normalizar_itemname(row.get("item_name") or "")
            nome_sanitizado = nome.replace(" ", "")
            completion = int(row.get("completion_state") or 0)

            if "efolioa" in nome_sanitizado:
                estado_aluno_a = completion
            elif "efoliob" in nome_sanitizado:
                estado_aluno_b = completion
            elif "efolioc" in nome_sanitizado:
                estado_aluno_c = completion
            elif "global" in nome_sanitizado:
                continue

        estado_a.append(estado_aluno_a)
        estado_b.append(estado_aluno_b)
        estado_c.append(estado_aluno_c)

    def percentagem(lista):
        return round(sum(lista) / len(lista) * 100, 1) if lista else 0.0

    resultado = {
        "E-fólio A": percentagem(estado_a),
        "E-fólio B": percentagem(estado_b)
    }

    if any(estado_c):
        resultado["E-fólio C"] = percentagem(estado_c)

    media_final = round(sum(resultado.values()) / len(resultado), 1) if resultado else 0.0

    final = {
        "por_atividade": resultado,
        "media": media_final
    }

    logger.debug("calcular_taxa_conclusao_efolios: resultado=%r", final)
    return final

def calcular_taxa_conclusao_formativas(completions, cursos, course_id):
    logger.debug("calcular_taxa_conclusao_formativas: início para course_id=%s", course_id)
    completions_df = pd.DataFrame(completions)
    alunos_ids = alunos_inscritos_uc(cursos, course_id)

    tipos_validos = ['page', 'resource', 'quiz', 'lesson']
    totais_percentuais = []

    for tipo in tipos_validos:
        completions_tipo = completions_df[
            (completions_df['course_id'] == course_id) &
            (completions_df['module_type'] == tipo)
        ]

        if completions_tipo.empty:
            continue

        atividades_ids = completions_tipo['course_module_id'].unique()
        total_atividades = len(atividades_ids)
        total_alunos = len(alunos_ids)

        if total_atividades == 0 or total_alunos == 0:
            continue

        interacoes_validas = completions_tipo[
            (completions_tipo['completion_state'] == 1) &
            (completions_tipo['user_id'].isin(alunos_ids))
        ]

        total_interacoes = len(interacoes_validas)
        total_possivel = total_atividades * total_alunos
        percentagem = round((total_interacoes / total_possivel) * 100, 1)
        totais_percentuais.append(percentagem)

    media_final = round(sum(totais_percentuais) / len(totais_percentuais)) if totais_percentuais else 0
    logger.debug("calcular_taxa_conclusao_formativas: média final=%s", media_final)
    return media_final

def calcular_ultima_participacao_forum(posts, user_id, course_id):
    logger.debug("calcular_ultima_participacao_forum: início para user_id=%s, course_id=%s", user_id, course_id)
    posts_professor = [
        p for p in posts
        if p["user_id"] == user_id and p["course_id"] == course_id
    ]
    if not posts_professor:
        logger.debug("calcular_ultima_participacao_forum: sem participações")
        return "—"

    mais_recente = max(posts_professor, key=lambda p: p["time_created"])
    dt = datetime.fromtimestamp(mais_recente["time_created"])
    resultado = dt.strftime("%d/%m/%Y %H:%M")
    logger.debug("calcular_ultima_participacao_forum: última participação=%s", resultado)
    return resultado

def gerar_barra_conclusao(label, valor):
    logger.debug("gerar_barra_conclusao: label=%s, valor=%s%%", label, valor)
    return html.Div(className="barra-container", children=[
        html.Div(label, className="barra-label"),
        html.Div(className="barra-fundo", children=[
            html.Div(className="barra-progresso", style={
                "width": f"{valor}%",
                "backgroundColor": "#9eff58"
            }),
            html.Div(f"{valor}%", className="barra-texto")
        ])
    ])

def gerar_semi_circulo(label, valor):
    logger.debug("gerar_semi_circulo: label=%s, valor=%s", label, valor)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        gauge={
            'shape': "angular",
            'axis': {'range': [0, 100]},
            'bar': {'color': "#9eff58"},
            'bgcolor': "#e6e6e6"
        },
        number={'font': {'size': 40}},
        title={"text": ""}
    ))
    fig.update_layout(
        margin=dict(t=20, b=0, l=0, r=0),
        height=100,
        width=130
    )

    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        style={"height": "140px", "width": "130px", "margin": "0 auto"}
    )

def bloco_conclusao_linha(nome, valor_gauge, labels, dados_conclusao):
    logger.debug("bloco_conclusao_linha: nome=%s, valor_gauge=%s, labels=%s", nome, valor_gauge, labels)
    return html.Div(className="bloco-conclusao-linha", children=[
        html.Div(className="bloco-conclusao-gauge", children=[
            gerar_semi_circulo(nome, valor_gauge)
        ]),
        html.Div(className="bloco-conclusao-barras", children=[
            html.Div(nome, style={"fontWeight": "bold", "marginBottom": "6px"}),
            *[gerar_barra_conclusao(label, dados_conclusao[label]) for label in labels]
        ])
    ])

def gerar_gauge_dashboard_professor(titulo, valor, cor):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        gauge={
            'shape': "angular",
            'axis': {'range': [0, 100]},
            'bar': {'color': cor},
            'bgcolor': "#f4faf4"
        },
        number={'font': {'size': 36}, 'valueformat': '.0f'},
        title={"text": ""}
    ))
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=180
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})

def obter_opcoes_dropdown_cursos(user_id):
    try:
        cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())
        cursos_user = cursos[cursos['user_id'] == user_id].copy()

        # Extrair o ano letivo de cada course_name
        cursos_user['ano_letivo'] = cursos_user['course_name'].apply(extrair_ano_letivo)

        # Determinar o ano letivo mais recente (atual)
        anos_validos = sorted(cursos_user['ano_letivo'].dropna().unique())
        if not anos_validos:
            return []
        ano_atual = anos_validos[-1]

        # Filtrar apenas as do ano atual
        cursos_filtrados = cursos_user[cursos_user['ano_letivo'] == ano_atual].copy()

        # Extrai uc_id para evitar duplicados
        cursos_filtrados['uc_id'] = cursos_filtrados['course_name'].str.extract(r'(\d{5})')

        # Ordenar e eliminar duplicados por uc_id
        cursos_ordenados = cursos_filtrados.sort_values(by="course_name", ascending=False)
        cursos_unicos = cursos_ordenados.drop_duplicates(subset=["uc_id"])

        opcoes = [
            {"label": linha['course_name'], "value": linha['course_id']}
            for _, linha in cursos_unicos.iterrows()
        ]

        logger.debug(f"[Dropdown] Ano letivo atual: {ano_atual}, opções: {opcoes}")
        return opcoes

    except Exception as e:
        logger.error("[ERRO] (obter_opcoes_dropdown_cursos):", exc_info=True)
        return []

def atualizar_topo_info_professor(novo_course_id, user_id):
    nome, papel, nome_curso = get_dashboard_top_info(user_id, novo_course_id)
    return f"[{papel}] {nome}", nome_curso

def contar_foruns_disponibilizados(dados, course_id):
    return sum(1 for d in dados if d["course_id"] == course_id and d["module_type"] == "forum")

def atualizar_dashboard_professor(course_id, user_id):
    try:
        dados_conteudos = qp.fetch_conteudos_disponibilizados_local()
        contagem = contar_conteudos_publicados(dados_conteudos, user_id, course_id)

        dados_forum = qg.fetch_all_forum_posts_local()
        dados_cursos = qg.fetch_all_user_course_data_local()
        topicos_criados, topicos_respondidos = contar_topicos_respostas_professor(dados_forum, user_id, course_id)
        velocidade = calcular_velocidade_resposta(dados_forum, user_id, course_id)
        ultima_participacao = calcular_ultima_participacao_forum(dados_forum, user_id, course_id)

        dados_acessos = qp.fetch_course_access_logs_local()
        media_acessos = calcular_media_acessos_semanal(dados_acessos, user_id, course_id)
        ultimo_acesso = obter_ultimo_acesso_uc(dados_acessos, user_id, course_id)

        dados_completions = qg.fetch_all_grade_progress_local()
        dados_medias = calcular_medias_efolios(dados_completions, dados_cursos, course_id)
        distribuicao = calcular_distribuicao_desempenho_global_professor(dados_completions, dados_cursos, course_id)

        taxa_conclusao = calcular_taxa_conclusao_efolios(dados_completions, dados_cursos, course_id)
        taxa_conclusao_formativas = calcular_taxa_conclusao_formativas(dados_completions, dados_cursos, course_id)

        return html.Div(children=[
            html.Div(children=[
                html.H2("Informação Geral do Docente", className="dashboard-titulo-geral")
            ]),

            html.Div(children=[
                html.H3("Docente - Nível de Interação", className="dashboard-aluno-professor-titulo")
            ]),

            html.Div(className="dashboard-professor-linha3colunas", children=[
                html.Div(className="dashboard-professor-coluna", children=[
                    render_card_acessos(media_acessos, ultimo_acesso)
                ]),
                html.Div(className="dashboard-professor-coluna", children=[
                    render_card_forum(topicos_criados, topicos_respondidos, velocidade, ultima_participacao)
                ]),
                html.Div(className="dashboard-professor-coluna", children=[
                    render_conteudos_publicados(contagem)
                ])
            ]),

            html.Div(children=[
                html.H3("Alunos - Desempenho", className="dashboard-aluno-professor-titulo")
            ]),

            render_card_conclusoes_gauge({
                "avaliativas": taxa_conclusao["media"],
                "formativas": taxa_conclusao_formativas
            }),

            render_card_mini_graficos(
                dados_medias,
                distribuicao
            )
        ])
    except Exception as e:
        logger.error("[ERRO] atualizar_dashboard_professor: %s", e, exc_info=True)
        return html.Div("Erro ao carregar os dados do dashboard.")

def register_callbacks(app):
    @app.callback(
        Output("info_nome_utilizador_professor", "children"),
        Output("info_nome_curso_professor", "children"),
        Input("dropdown_uc_professor", "value"),
        State("store_user_id_professor", "data")
    )
    def atualizar_topo_info_professor(novo_course_id, user_id):
        nome, papel, nome_curso = get_dashboard_top_info(user_id, novo_course_id)
        return f"[{papel}] {nome}", nome_curso

    @app.callback(
        Output("conteudo_dashboard_professor", "children"),
        Input("dropdown_uc_professor", "value"),
        State("store_user_id_professor", "data")
    )
    def callback_dashboard_professor(course_id, user_id):
        return atualizar_dashboard_professor(course_id, user_id)

# =========================
# Layout principal
# =========================

def layout(user_id):
    try:
        cursos = pd.DataFrame(qg.fetch_all_user_course_data_local())
        cursos_user = cursos[cursos['user_id'] == user_id].copy()

        cursos_user['ano_letivo'] = cursos_user['course_name'].apply(extrair_ano_letivo)
        anos_validos = sorted(cursos_user['ano_letivo'].dropna().unique())
        ano_atual = anos_validos[-1] if anos_validos else None

        cursos_user['uc_id'] = cursos_user['course_name'].str.extract(r'(\d{5})')
        cursos_ordenados = cursos_user.sort_values(by="course_name", ascending=False)
        cursos_unicos = cursos_ordenados.drop_duplicates(subset=["uc_id"]).copy()
        cursos_ano_atual = cursos_unicos[cursos_unicos['ano_letivo'] == ano_atual]

        course_id = cursos_ano_atual['course_id'].values[0] if not cursos_ano_atual.empty else None

        dados_conteudos = qp.fetch_conteudos_disponibilizados_local()
        contagem = contar_conteudos_publicados(dados_conteudos, user_id, course_id)

        dados_forum = qg.fetch_all_forum_posts_local()
        dados_cursos = qg.fetch_all_user_course_data_local()

        topicos_criados, topicos_respondidos = contar_topicos_respostas_professor(dados_forum, user_id, course_id)
        velocidade = calcular_velocidade_resposta(dados_forum, user_id, course_id)
        ultima_participacao = calcular_ultima_participacao_forum(dados_forum, user_id, course_id)

        dados_acessos = qp.fetch_course_access_logs_local()
        media_acessos = calcular_media_acessos_semanal(dados_acessos, user_id, course_id)
        ultimo_acesso = obter_ultimo_acesso_uc(dados_acessos, user_id, course_id)

        dados_completions = qg.fetch_all_grade_progress_local()
        dados_medias = calcular_medias_efolios(dados_completions, dados_cursos, course_id)
        distribuicao = calcular_distribuicao_desempenho_global_professor(dados_completions, dados_cursos, course_id)

        taxa_conclusao = calcular_taxa_conclusao_efolios(dados_completions, dados_cursos, course_id)
        taxa_conclusao_formativas = calcular_taxa_conclusao_formativas(dados_completions, dados_cursos, course_id)

    except Exception as e:
        print("[ERRO] (layout) Falha ao gerar o dashboard do professor.")
        traceback.print_exc()
        return html.Div("Erro ao ligar à base de dados.")

    return html.Div(children=[
        dcc.Store(id="store_user_id_professor", data=user_id),
        html.Div(className="topo-dashboard", children=[
            html.Div(className="linha-superior", children=[
                html.Div(className="info-utilizador", children=[
                    DashIconify(
                        icon="mdi:teach",
                        width=32,
                        color="#2c3e50",
                        className="avatar-icon"
                    ),
                    html.Span(id="info_nome_utilizador_professor", className="nome-utilizador")
                ]),
                html.Div(className="dropdown-curso", children=[
                    dcc.Dropdown(
                        id="dropdown_uc_professor",
                        options=obter_opcoes_dropdown_cursos(user_id),
                        value=course_id,
                        clearable=False,
                        className="dropdown-uc-selector"
                    )
                ])
            ]),
            html.Div(className="barra-uc", children=[
                html.Span(id="info_nome_curso_professor", className="nome-curso"),
                html.Span(extrair_ano_letivo(get_dashboard_top_info(user_id, course_id)[2]) or "", className="ano-letivo")
            ])
        ]),

        html.Div(id="conteudo_dashboard_professor", children=[
            html.Div(children=[
                html.H2("Informação Geral do Docente", className="dashboard-titulo-geral")
            ]),
            html.Div(children=[
                html.H3("Docente - Nível de Interação", className="dashboard-aluno-professor-titulo")
            ]),

            html.Div(className="dashboard-professor-linha3colunas", children=[
                html.Div(className="dashboard-professor-coluna", children=[
                    render_card_acessos(media_acessos, ultimo_acesso)
                ]),
                html.Div(className="dashboard-professor-coluna", children=[
                    render_card_forum(topicos_criados, topicos_respondidos, velocidade, ultima_participacao)
                ]),
                html.Div(className="dashboard-professor-coluna", children=[
                    render_conteudos_publicados(contagem)
                ])
            ]),

            html.Div(children=[
                html.H3("Alunos - Desempenho", className="dashboard-aluno-professor-titulo")
            ]),

            render_card_conclusoes_gauge({
                "avaliativas": taxa_conclusao["media"],
                "formativas": taxa_conclusao_formativas
            }),

            render_card_mini_graficos(
                dados_medias,
                distribuicao
            )
        ])
    ])

# =========================
# Componentes visuais
# =========================

def render_conteudos_publicados(contagem):
    icons = {
        "Ficheiros": "mdi:folder-outline",
        "Páginas": "mdi:file-document-outline",
        "Links": "mdi:link-variant",
        "Livros": "mdi:book-open-page-variant",
        "Pastas": "mdi:folder-outline",
        "Quizzes": "mdi:clipboard-outline",
        "Lições": "mdi:book-education-outline",
        "Fóruns": "mdi:forum-outline" ,
        "Conteúdos Multimédia": "mdi:video-box" 
    }
    cores = ["bg-yellow", "bg-green", "bg-darkgreen", "bg-blue", "bg-orange", "bg-teal", "bg-purple", "bg-lightblue","bg-pink"]

    return html.Div(className="card card-volume", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Recursos Pedagógicos", className="tooltip-hover card-section-title"),
            html.Span(
                "Mostra a contagem de recursos pedagógicos disponibilizados pelo professor na UC.\n"
                "- Ficheiros\n"
                "- Páginas\n"
                "- Quizzes\n"
                "- Pastas\n"
                "  etc.",
                className="tooltip-text"
            )
        ]),
        html.Ul(className="volume-list", children=[
            html.Li(className="volume-item", children=[
                html.Div(className=f"volume-icon-bg {cores[i]}", children=[
                    DashIconify(icon=icons[tipo], width=24, color="white")
                ]),
                html.Span(tipo),
                html.Span(str(contagem.get(tipo, 0)), className="volume-number")
            ]) for i, tipo in enumerate(icons)
        ])
    ])


def render_card_forum(criados, respondidos, velocidade, ultima_participacao):
    return html.Div(className="card dashboard-professor-card-forum", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Fórum", className="tooltip-hover dashboard-professor-card-title"),
            html.Span(
                "Mostra a participação do docente nos fóruns da UC.\n"
                "- Tópicos Criados: tópicos iniciados pelo professor\n"
                "- Tópicos Respondidos: respostas dadas a mensagens dos alunos\n"
                "- Tempo de Resposta: tempo médio entre uma questão de aluno e a resposta do professor\n"
                "- Última Participação: data e hora da última interação no fórum",
                className="tooltip-text"
            )
        ]),
        html.Div(className="dashboard-professor-forum-box", children=[
            html.Div(className="dashboard-professor-forum-item", children=[
                DashIconify(icon="mdi:email-outline", width=28, color="white"),
                html.Div("Tópicos Criados", className="dashboard-professor-forum-label"),
                html.Div(str(criados), className="dashboard-professor-forum-numero")
            ]),
            html.Div(className="dashboard-professor-forum-item", children=[
                DashIconify(icon="mdi:email-send-outline", width=28, color="white"),
                html.Div("Tópicos Respondidos", className="dashboard-professor-forum-label"),
                html.Div(str(respondidos), className="dashboard-professor-forum-numero")
            ]),
            html.Div(className="dashboard-professor-forum-item", children=[
                DashIconify(icon="mdi:clock-outline", width=28, color="white"),
                html.Div("Tempo de Resposta", className="dashboard-professor-forum-label"),
                html.Div(velocidade if velocidade is not None else "—", className="dashboard-professor-forum-numero")
            ]),
            html.Div(className="dashboard-professor-forum-item", children=[
                DashIconify(icon="mdi:account-arrow-right-outline", width=28, color="white"),
                html.Div("Última Participação", className="dashboard-professor-forum-label"),
                html.Div(ultima_participacao, className="dashboard-professor-forum-numero")
            ])
        ])
    ])


def render_card_medias_classificacao(dados):
    labels = list(dados.keys())
    valores = list(dados.values())
    cores = ["#f4f7b6", "#d4d4d4", "#195350", "#45b39c"]

    fig = go.Figure(go.Bar(
        x=valores,
        y=labels,
        orientation='h',
        marker=dict(color=cores),
        text=valores,
        textposition="auto"
    ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=200,
        yaxis=dict(autorange="reversed"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        autosize=True  
    )

    return html.Div(className="card-bloco", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Média de classificações por atividade", className="tooltip-hover card-section-title"),
            html.Span(
                "Mostra a média das classificações obtidas pelos alunos nas atividades de avaliação.\n"
                "Considera apenas os e-fólios realizados por alunos em regime de Avaliação Contínua.",
                className="tooltip-text"
            )
        ]),
        html.Div(style={"width": "100%", "height": "100%"}, children=[
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False, "responsive": True}, 
                style={"width": "100%"}  
            )
        ])
    ])

def render_card_mini_graficos(medias, distribuicao):
    return html.Div(className="bloco-mini-graficos", children=[
        render_card_medias_classificacao(medias),
        render_card_estado_global(distribuicao)
    ])

def render_card_estado_global(distribuicao):
    # Ordem garantida
    estados = ["Crítico", "Em Risco", "Expectável"]
    valores = [distribuicao.get(e, 0) for e in estados]
    cores = ["#ec6c6c", "#f7c948", "#63c78d"] # vermelho, amarelo, verde

    fig = go.Figure(data=[go.Pie(
        labels=estados,
        values=valores,
        hole=0.4,
        marker=dict(colors=cores),
        sort=False  # mantém a ordem
    )])

    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        height=200
    )

    return html.Div(className="card-bloco", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Desempenho Global", className="tooltip-hover card-section-title"),
            html.Span(
                "Mostra a distribuição do desempenho global dos alunos com base nas notas dos e-fólios.\n"
                "A categorização segue os critérios:\n"
                "- Expectável: soma ≥ 4.5 valores\n"
                "- Em Risco: entre 3.5 e 4.5 valores\n"
                "- Crítico: abaixo de 3.5 valores\n"
                "- Não Aplicável: alunos fora do regime de Avaliação Contínua",
                className="tooltip-text"
            )
        ]),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "160px"})
    ])

def render_topo_geral(user_id, course_id):
    nome, papel, curso = get_dashboard_top_info(user_id, course_id)
    ano_curso_atual = extrair_ano_letivo(curso) or ""
    return html.Div(className="topo-dashboard", children=[
        html.Div(className="linha-superior", children=[
            html.Div(className="info-utilizador", children=[
                DashIconify(
                    icon="mdi:school" if papel == "ALUNO" else "mdi:teach",
                    width=32,
                    color="#2c3e50",
                    className="avatar-icon"
                ),
                html.Span(id="info_nome_utilizador_professor", className="nome-utilizador")
            ])
        ]),
        html.Div(className="barra-uc", children=[
            html.Span(id="info_nome_curso_professor", className="nome-curso"),
            html.Span(ano_curso_atual, className="ano-letivo")
        ])
    ])

def render_card_acessos(media_acessos, ultimo_acesso):
    return html.Div(className="card dashboard-professor-card-acessos", children=[
        html.Div(className="tooltip-bloco", children=[
            html.H4("Acessos ao Curso", className="tooltip-hover dashboard-professor-card-title"),
            html.Span(
                "Mostra os padrões de acesso do professor ao curso no Moodle.\n"
                "- Último Acesso: data do acesso mais recente registado\n"
                "- Média de acessos (semanal): número médio de vezes que o professor acede à área do curso por semana",
                className="tooltip-text"
            )
        ]),
        html.Div(className="dashboard-professor-acessos-box", children=[
            html.Div(className="dashboard-professor-acesso-item", children=[
                DashIconify(icon="mdi:calendar-clock", width=28, color="white"),
                html.Div("Último Acesso", className="dashboard-professor-acesso-label"),
                html.Div(ultimo_acesso, className="dashboard-professor-acesso-numero")
            ]),
            html.Div(className="dashboard-professor-acesso-item", children=[
                DashIconify(icon="mdi:account-clock-outline", width=28, color="white"),
                html.Div("Média de acessos (semanal)", className="dashboard-professor-acesso-label"),
                html.Div(f"{int(round(media_acessos))} acessos/semana", className="dashboard-professor-acesso-numero")
            ])
        ])
    ])

def render_card_conclusoes_gauge(valores_gauge):
    return html.Div(className="dashboard-professor-gaugue-linha", children=[
        html.Div(children=[
            html.Div(className="tooltip-bloco", children=[
                html.H4("Taxa de conclusão das avaliações", className="tooltip-hover card-section-title"),
                html.Span(
                    "Mostra a percentagem média de alunos que concluíram os e-fólios.\n"
                    "Considera apenas os alunos em regime de Avaliação Contínua.",
                    className="tooltip-text"
                )
            ]),
            gerar_gauge_dashboard_professor("", valores_gauge["avaliativas"], "#b6f7c3")
        ], className="dashboard-professor-gauge-card"),
        html.Div(children=[
            html.Div(className="tooltip-bloco", children=[
                html.H4("Taxa de conclusão das atividades", className="tooltip-hover card-section-title"),
                html.Span(
                    "Mostra a percentagem média de conclusão das atividades formativas (ficheiros, quizzes, páginas, etc.) por parte dos alunos inscritos na UC.",
                    className="tooltip-text"
                )
            ]),
            gerar_gauge_dashboard_professor("", valores_gauge["formativas"], "#b2d7d5")
        ], className="dashboard-professor-gauge-card")
    ])