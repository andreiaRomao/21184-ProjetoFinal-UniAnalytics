from dash import html, dcc
from dash_iconify import DashIconify
import queries.queriesProfessor as qp
import queries.queriesGeral as qg
import queries.queriesAluno as qa
import plotly.graph_objects as go
import plotly.express as px
import traceback
import pandas as pd
import re
import unicodedata
from datetime import datetime
from collections import defaultdict # para contagem de acessos semanais

from dashboards.dashboardGeral import layout as layout_geral

# =========================
# Funções de lógica modular
# =========================

def normalizar_nome_item(texto):
    """Remove acentos e normaliza o nome dos itens."""
    if not texto:
        return ""
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    texto = texto.lower()
    texto = texto.replace('-', ' ').replace('_', ' ').strip()
    return texto

def alunos_inscritos_uc(cursos, course_id):
    cursos_df = pd.DataFrame(cursos)
    return cursos_df[
        (cursos_df['courseid'] == course_id) &
        (cursos_df['role'] == 'student')
    ]['userid'].unique()

def filtrar_alunos_avaliacao_continua(cursos, course_id):
    cursos_df = pd.DataFrame(cursos)
    estudantes = cursos_df[
        (cursos_df['courseid'] == course_id) &
        (cursos_df['role'] == 'student')
    ].copy()
    estudantes['grupo'] = estudantes['groupname'].fillna('').str.lower()
    return estudantes[estudantes['grupo'].str.contains('aval')]['userid'].unique()

def contar_conteudos_publicados(dados, professor_id, course_id):
    tipos = {
        'resource': 'Ficheiros',
        'page': 'Páginas',
        'url': 'Links',
        'book': 'Livros',
        'folder': 'Pastas',
        'quiz': 'Quizzes',
        'lesson': 'Lições' 
    }
    contagem = {nome: 0 for nome in tipos.values()}
    for d in dados:
        if d['course_id'] == course_id:
            tipo_raw = d.get('module_type')
            if tipo_raw in tipos:
                contagem[tipos[tipo_raw]] += 1
    return contagem

def contar_topicos_respostas_professor(dados, professor_id, course_id):
    criados = sum(1 for d in dados if d['userid'] == professor_id and d['course_id'] == course_id and d['post_type'] == 'topic')
    respondidos = sum(1 for d in dados if d['userid'] == professor_id and d['course_id'] == course_id and d['post_type'] == 'reply')
    return criados, respondidos

def calcular_velocidade_resposta(posts, professor_id, course_id):  
    posts_curso = [p for p in posts if p["course_id"] == course_id]

    # Indexar posts por ID
    posts_por_id = {p["post_id"]: p for p in posts_curso}

    # Filtrar TODOS os posts feitos por aluno
    posts_aluno = [
        p for p in posts_curso 
        if "student" in (p.get("role") or "").lower()
    ]

    tempos_resposta = []

    for post_aluno in posts_aluno:
        post_id = post_aluno["post_id"]
        tempo_post = datetime.fromtimestamp(post_aluno["timecreated"])

        # Procurar respostas diretas feitas por professor
        respostas_professor = [
            p for p in posts_curso
            if p.get("parent") == post_id and "teacher" in (p.get("role") or "").lower()
        ]

        if respostas_professor:
            resposta = min(respostas_professor, key=lambda p: p["timecreated"])
            tempo_resposta = datetime.fromtimestamp(resposta["timecreated"])
            delta_dias = (tempo_resposta - tempo_post).total_seconds() / (3600 * 24)
            tempos_resposta.append(delta_dias)

    if tempos_resposta:
        media_dias = sum(tempos_resposta) / len(tempos_resposta) 
        dias = int(media_dias)
        horas = round((media_dias - dias) * 24)
        return f"{dias} dia{'s' if dias != 1 else ''} e {horas} horas"
    else:
        return None

def calcular_media_acessos_semanal(acessos, professor_id, course_id):
    # Filtra apenas acessos do professor ao curso
    acessos_prof = [
        a for a in acessos
        if a["userid"] == professor_id and a["courseid"] == course_id
    ]

    # Agrupa por ano+semana
    semanas = defaultdict(int)
    for acesso in acessos_prof:
        dt = acesso["access_time"]
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        ano_semana = dt.strftime("%Y-%W")
        semanas[ano_semana] += 1

    if semanas:
        media = sum(semanas.values()) / len(semanas)
        return round(media, 1)
    else:
        return 0

def calcular_distribuicao_desempenho_global_professor(completions, cursos, course_id):
    # Converte as listas recebidas para DataFrame
    completions_df = pd.DataFrame(completions)
    cursos_df = pd.DataFrame(cursos)

    distribuicao = {"Crítico": 0, "Em Risco": 0, "Expectável": 0}
    
    # Filtrar apenas alunos inscritos como estudantes no curso
    estudantes = cursos_df[
        (cursos_df['courseid'] == course_id) &
        (cursos_df['role'] == 'student')
    ].copy()

    # Normalizar nome do grupo
    estudantes['grupo'] = estudantes['groupname'].fillna('').str.lower()
    
    # Filtrar só os da Avaliação Contínua
    alunos_aval = estudantes[estudantes['grupo'].str.contains('aval')]
    alunos_ids = alunos_aval['userid'].unique()

    for aluno_id in alunos_ids:
        # Filtrar todas as notas deste aluno no curso
        notas_aluno = completions_df[
            (completions_df['userid'] == aluno_id) &
            (completions_df['course_id'] == course_id) &
            (completions_df['module_type'] == 'assign')
        ]

        soma = 0.0
        for _, linha in notas_aluno.iterrows():
            nome_item = (linha.get("itemname") or "").lower()
            if "efolio" in nome_item:
                try:
                    soma += float(linha["finalgrade"])
                except (ValueError, TypeError):
                    continue

        # Classificar aluno
        if soma < 3.5:
            classificacao = "Crítico"
        elif soma < 4.5:
            classificacao = "Em Risco"
        else:
            classificacao = "Expectável"

        distribuicao[classificacao] += 1

    return distribuicao

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

def extrair_ano_letivo(course_name):
    
    match = re.search(r'_(\d{2})', course_name)
    if match:
        sufixo = int(match.group(1))
        ano_inicio = 2000 + sufixo
        return f"{ano_inicio}/{ano_inicio + 1}"
    return None

def obter_ultimo_acesso_uc(acessos, professor_id, course_id):
    acessos_filtrados = [
        a for a in acessos
        if a["userid"] == professor_id and a["courseid"] == course_id
    ]
    if not acessos_filtrados:
        return "—"
    mais_recente = max(acessos_filtrados, key=lambda a: a["access_time"])
    dt = mais_recente["access_time"]
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d/%m/%Y")

def calcular_medias_efolios(completions, cursos, course_id):
    completions_df = pd.DataFrame(completions)
    alunos_aval = filtrar_alunos_avaliacao_continua(cursos, course_id)

    # Listas de notas
    notas_a, notas_b, notas_c = [], [], []

    for aluno_id in alunos_aval:
        notas_aluno = completions_df[
            (completions_df['userid'] == aluno_id) &
            (completions_df['course_id'] == course_id) &
            (completions_df['module_type'] == 'assign')
        ]

        nota_a = nota_b = nota_c = 0.0

        for _, row in notas_aluno.iterrows():
            nome = normalizar_nome_item(row.get("itemname"))
            nota = float(row.get("finalgrade") or 0)

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
    return resultado


def calcular_taxa_conclusao_efolios(completions, cursos, course_id):
    completions_df = pd.DataFrame(completions)
    alunos_aval = filtrar_alunos_avaliacao_continua(cursos, course_id)

    estado_a, estado_b, estado_c = [], [], []

    for aluno_id in alunos_aval:
        notas_aluno = completions_df[
            (completions_df["userid"] == aluno_id) &
            (completions_df["course_id"] == course_id) &
            (completions_df["module_type"] == "assign")
        ]

        estado_aluno_a = estado_aluno_b = estado_aluno_c = 0  # ← por default: 0 (não entregou)

        for _, row in notas_aluno.iterrows():
            nome = normalizar_nome_item(row.get("itemname") or "")
            nome_sanitizado = nome.replace(" ", "")
            completion = int(row.get("completionstate") or 0)

            if "efolioa" in nome_sanitizado:
                estado_aluno_a = completion
            elif "efoliob" in nome_sanitizado:
                estado_aluno_b = completion
            elif "efolioc" in nome_sanitizado:
                estado_aluno_c = completion
            elif "global" in nome_sanitizado:
                continue  # exclui global

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

    return {
        "por_atividade": resultado,
        "media": media_final
    }

def calcular_taxa_conclusao_formativas(completions, cursos, course_id):
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

        atividades_ids = completions_tipo['coursemodule_id'].unique()

        total_atividades = len(atividades_ids)
        total_alunos = len(alunos_ids)

        if total_atividades == 0 or total_alunos == 0:
            continue

        # Total de interações válidas
        interacoes_validas = completions_tipo[
            (completions_tipo['completionstate'] == 1) &
            (completions_tipo['userid'].isin(alunos_ids))
        ]

        total_interacoes = len(interacoes_validas)

        # Taxa de conclusão por tipo
        total_possivel = total_atividades * total_alunos
        percentagem = round((total_interacoes / total_possivel) * 100, 1)

        totais_percentuais.append(percentagem)

    # Média das percentagens de todos os tipos
    media_final = round(sum(totais_percentuais) / len(totais_percentuais)) if totais_percentuais else 0

    return media_final

def calcular_ultima_participacao_forum(posts, professor_id, course_id):
    posts_professor = [
        p for p in posts
        if p["userid"] == professor_id and p["course_id"] == course_id
    ]
    if not posts_professor:
        return "—"

    mais_recente = max(posts_professor, key=lambda p: p["timecreated"])
    dt = datetime.fromtimestamp(mais_recente["timecreated"])
    return dt.strftime("%d/%m/%Y %H:%M")

def gerar_barra_conclusao(label, valor):
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

    return html.Div(className="dashboard-professor-gauge-card", children=[
        html.H4(titulo, className="dashboard-professor-gauge-titulo"),
        dcc.Graph(figure=fig, config={"displayModeBar": False})
    ])

# =========================
# Layout principal
# =========================

def layout(professor_id, course_id):
    try:
        dados_conteudos = qp.fetch_conteudos_disponibilizados()
        contagem = contar_conteudos_publicados(dados_conteudos, professor_id, course_id)

        dados_forum = qg.fetch_all_forum_posts()
        dados_cursos = qg.fetch_user_course_data() 

        topicos_criados, topicos_respondidos = contar_topicos_respostas_professor(dados_forum, professor_id, course_id)
        velocidade = calcular_velocidade_resposta(dados_forum, professor_id, course_id)
        ultima_participacao = calcular_ultima_participacao_forum(dados_forum, professor_id, course_id)

        dados_acessos = qp.fetch_course_access_logs()
        media_acessos = calcular_media_acessos_semanal(dados_acessos, professor_id, course_id)
        ultimo_acesso = obter_ultimo_acesso_uc(dados_acessos, professor_id, course_id)

        dados_completions = qa.fetch_all_completions()
        dados_medias = calcular_medias_efolios(dados_completions, dados_cursos, course_id)
        distribuicao = calcular_distribuicao_desempenho_global_professor(dados_completions, dados_cursos, course_id)

        taxa_conclusao = calcular_taxa_conclusao_efolios(dados_completions, dados_cursos, course_id)
        taxa_conclusao_formativas = calcular_taxa_conclusao_formativas(dados_completions, dados_cursos, course_id)

    except Exception as e:
        print("[ERRO] (layout) Falha ao gerar o dashboard do professor.")
        traceback.print_exc()
        return html.Div("Erro ao ligar à base de dados.")

    return html.Div(children=[
        render_topo_geral(professor_id, course_id),

        html.Div(children=[
            html.H2("Informação Geral do Docente", style={
                "fontSize": "26px",
                "fontWeight": "bold",
                "color": "#2c3e50",
                "marginBottom": "8px",
                "text-align": "center"
            })
        ]),

        html.Div(
            children=[
                html.H3("Docente - Nível de Interação", className="dashboard-aluno-professor-titulo")
            ],
            style={"marginTop": "0px", "paddingTop": "0px", "marginBottom": "0px", "paddingBottom": "0px"}
        ),

        html.Div(className="dashboard-professor-linha3colunas", children=[
            html.Div(className="dashboard-professor-coluna", children=[
                render_card_forum(topicos_criados, topicos_respondidos, velocidade, media_acessos, ultima_participacao)
            ]),
            html.Div(className="dashboard-professor-coluna", children=[
                render_card_acessos(media_acessos, ultimo_acesso)
            ]),
            html.Div(className="dashboard-professor-coluna", children=[
                render_conteudos_publicados(contagem)
            ])
        ]),

        html.Div(
            children=[
                html.H3("Alunos - Desempenho", className="dashboard-aluno-professor-titulo")
            ],
            style={"marginTop": "0px", "paddingTop": "0px", "marginBottom": "0px", "paddingBottom": "0px"}
        ),

        render_card_conclusoes_gauge({
            "avaliativas": taxa_conclusao["media"],
            "formativas": taxa_conclusao_formativas
        }),

        render_card_mini_graficos(
            dados_medias,
            distribuicao
        )
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
        "Conteúdos Multimédia": "mdi:video-box" 
    }
    cores = ["bg-yellow", "bg-green", "bg-darkgreen", "bg-blue", "bg-orange", "bg-teal","bg-purple", "bg-pink"]

    return html.Div(className="card card-volume", children=[
        html.H4("Recursos Pedagógicos", className="card-section-title"),
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

def render_card_forum(criados, respondidos, velocidade, media_acessos, ultima_participacao):
    return html.Div(className="card dashboard-professor-card-forum", children=[
        html.H4("Fórum - Tópicos", className="dashboard-professor-card-title"),
        html.Div(className="dashboard-professor-forum-box", children=[
            html.Div(className="dashboard-professor-forum-item dashboard-professor-forum-item-criados", children=[
                DashIconify(icon="mdi:email-outline", width=28, color="white"),
                html.Div("Criados", className="dashboard-professor-forum-label"),
                html.Div(str(criados), className="dashboard-professor-forum-numero")
            ]),
            html.Div(className="dashboard-professor-forum-item dashboard-professor-forum-item-respondidos", children=[
                DashIconify(icon="mdi:email-send-outline", width=28, color="white"),
                html.Div("Respondidos", className="dashboard-professor-forum-label"),
                html.Div(str(respondidos), className="dashboard-professor-forum-numero")
            ]),
            html.Div(className="dashboard-professor-forum-item dashboard-professor-forum-item-velocidade", children=[
                DashIconify(icon="mdi:clock-outline", width=28, color="white"),
                html.Div("Velocidade de Resposta", className="dashboard-professor-forum-label"),
                html.Div(velocidade if velocidade is not None else "—", className="dashboard-professor-forum-numero")
            ]),
            html.Div(className="dashboard-professor-forum-item dashboard-professor-forum-item-participacao", children=[
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
        plot_bgcolor="white"
    )

    return html.Div(className="card-bloco", children=[
        html.H4("Média de classificações por atividade", className="card-section-title"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "160px"})
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
        html.H4("Desempenho Global", className="card-section-title"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "160px"})
    ])

def render_topo_geral(userid, course_id):
    nome, papel, curso = get_dashboard_top_info(userid, course_id)
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
                html.Span(f"[{papel}] {nome}", className="nome-utilizador")
            ])
        ]),
        html.Div(className="barra-uc", children=[
            html.Span(curso, className="nome-curso"),
            html.Span(ano_curso_atual, className="ano-letivo")
        ])
    ])

def render_card_acessos(media_acessos, ultimo_acesso):
    return html.Div(className="card dashboard-professor-card-acessos", children=[
        html.H4("Acessos ao Curso", className="dashboard-professor-card-title"),
        html.Div(className="dashboard-professor-acessos-box", children=[
            html.Div(className="dashboard-professor-acesso-item", children=[
                DashIconify(icon="mdi:account-clock-outline", width=28, color="white"),
                html.Div("Média de acessos (semanal)", className="dashboard-professor-acesso-label"),
                html.Div(f"{int(round(media_acessos))} acessos/semana", className="dashboard-professor-acesso-numero")
            ]),
            html.Div(className="dashboard-professor-acesso-item dashboard-professor-acesso-item-claro", children=[
                DashIconify(icon="mdi:calendar-clock", width=28, color="white"),
                html.Div("Último Acesso", className="dashboard-professor-acesso-label"),
                html.Div(ultimo_acesso, className="dashboard-professor-acesso-numero")
            ])
        ])
    ])

def render_card_conclusoes_gauge(valores_gauge):
    return html.Div(className="dashboard-professor-gaugue-linha", children=[
        gerar_gauge_dashboard_professor("Taxa de conclusão das avaliações", valores_gauge["avaliativas"], "#b6f7c3"),
        gerar_gauge_dashboard_professor("Taxa de conclusão das atividades", valores_gauge["formativas"], "#b2d7d5")
    ])
