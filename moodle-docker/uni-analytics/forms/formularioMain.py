from forms import formularioPre, formularioPos, formulariosAdmin
from utils.logger import logger
from db.uniAnalytics import connect_to_uni_analytics_db
from datetime import datetime, timedelta
from dash import html

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