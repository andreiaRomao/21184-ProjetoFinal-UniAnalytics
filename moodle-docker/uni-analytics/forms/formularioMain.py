from forms import formularioPre, formularioPos, formulariosAdmin
from utils.logger import logger
from db.uniAnalytics import connect_to_uni_analytics_db
from datetime import datetime, timedelta
from dash import html, dcc

# Função que devolve o layout com base na rota atual, validando janela temporal
def get_layout(pathname, user_id, item_id):
    logger.debug(f"[Router] Pedido de layout para rota: {pathname} com item_id={item_id}")

    # Se for admin, não valida item_id
    if pathname == "/forms/formularioAdmin":
        logger.info("A carregar layout: administração de formulários")
        return formulariosAdmin.layout()

    # Validação para pre e pos
    if item_id <= 0:
        logger.warning(f"[Router] item_id inválido: {item_id}")
        return html.Div("Item inválido.")

    conn = connect_to_uni_analytics_db()
    cursor = conn.cursor()

    # Buscar dados do e-fólio
    cursor.execute("""
        SELECT name, start_date, end_date
        FROM efolios
        WHERE item_id = ?
        LIMIT 1
    """, (item_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        logger.warning(f"[Router] item_id {item_id} não encontrado na tabela efolios.")
        return html.Div("Formulário não disponível.")

    name, start_date_str, end_date_str = row
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()

    if pathname == "/forms/formularioPre":
        janela_inicio = start_date - timedelta(days=7)
        janela_fim = start_date
        if not (janela_inicio <= now <= janela_fim):
            logger.warning(f"[Router] Fora da janela do formulário pré para item_id={item_id}.")
            return html.Div("O formulário de pré-avaliação só está disponível na semana anterior ao início do e-fólio.")
        logger.info("A carregar layout: formulário de pré-avaliação")
        return formularioPre.layout(user_id, item_id)

    elif pathname == "/forms/formularioPos":
        janela_inicio = end_date
        janela_fim = end_date + timedelta(days=7)
        if not (janela_inicio <= now <= janela_fim):
            logger.warning(f"[Router] Fora da janela do formulário pós para item_id={item_id}.")
            return html.Div("O formulário de pós-avaliação só está disponível na semana após o fim do e-fólio.")
        logger.info("A carregar layout: formulário de pós-avaliação")
        return formularioPos.layout(user_id, item_id)

    logger.warning(f"[Router] Rota não reconhecida: {pathname}")
    return None

def listar_formularios_disponiveis(user_id):
    try:
        logger.debug("[Formulários] A verificar formulários disponíveis...")
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        # Verifica se o aluno pertence ao grupo "Avaliação Continua"
        cursor.execute("""
            SELECT group_name
            FROM course_data
            WHERE user_id = ?
            LIMIT 1
        """, (user_id,))
        resultado = cursor.fetchone()

        if not resultado or not resultado[0] or "continua" not in resultado[0].lower():
            logger.info("[Formulários] Aluno não pertence a Avaliação Contínua. Não mostrar formulários.")
            return html.Div([
                html.H3("Formulários de Avaliação Disponíveis", className="home-bloco-titulo"),
                html.Div("Os formulários de Avaliação só estão disponíveis para alunos de Avaliação Contínua.")
            ])

        cursor.execute("""
            SELECT item_id, name, course_name, available_pre, available_pos
            FROM efolios
            WHERE available_pre = 1 OR available_pos = 1
            ORDER BY start_date DESC
        """)
        resultados = cursor.fetchall()
        conn.close()

        logger.debug(f"[Formulários] Formularios encontrados: {len(resultados)}")

        componentes = []
        for item_id, nome, curso, pre, pos in resultados:
            texto_base = f"{curso} - {nome}"

            if pre:
                logger.debug(f"[Formulários] Disponível Pré: {texto_base} (item_id={item_id})")
                componentes.append(
                    dcc.Link(f"→ Inquérito Pré: {texto_base}", href=f"/forms/formularioPre?item_id={item_id}", className="btn-suave")
                )
            if pos:
                logger.debug(f"[Formulários] Disponível Pós: {texto_base} (item_id={item_id})")
                componentes.append(
                    dcc.Link(f"→ Inquérito Pós: {texto_base}", href=f"/forms/formularioPos?item_id={item_id}", className="btn-suave")
                )

        if not componentes:
            logger.info("[Formulários] Nenhum formulário de avaliação disponível.")
            return html.Div([
                html.H3("Formulários de Avaliação Disponíveis", className="home-bloco-titulo"),
                html.Div("Nenhum formulário de avaliação disponível neste momento.")
            ])

        return html.Div([
            html.H3("Formulários de Avaliação Disponíveis", className="home-bloco-titulo"),
            html.Div(componentes)
        ])

    except Exception as e:
        logger.error("[ERRO] (listar_formularios_disponiveis):", exc_info=True)
        return html.Div([
            html.H3("Formulários de Avaliação Disponíveis", className="home-bloco-titulo"),
            html.Div("Erro ao carregar formulários disponíveis.")
        ])