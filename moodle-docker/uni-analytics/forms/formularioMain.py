from forms import formularioPre, formularioPos, formulariosAdmin
from utils.logger import logger

# Função que devolve o layout com base na rota atual
def get_layout(pathname):
    logger.debug(f"[Router] Pedido de layout para rota: {pathname}")
    
    if pathname == "/forms/formularioPre":
        logger.info("A carregar layout: formulário de pré-avaliação")
        return formularioPre.layout()
    
    elif pathname == "/forms/formularioPos":
        logger.info("A carregar layout: formulário de pós-avaliação")
        return formularioPos.layout()
    
    elif pathname == "/forms/formularioAdmin":
        logger.info("A carregar layout: administração de formulários")
        return formulariosAdmin.layout()
    
    logger.warning(f"[Router] Rota não reconhecida: {pathname}")
    return None

# Registo dos callbacks de cada componente
def register_callbacks(app):
    logger.info("A registar callbacks dos formulários...")
    
    try:
        formularioPre.register_callbacks(app)
        formularioPos.register_callbacks(app)
        formulariosAdmin.register_callbacks(app)
        logger.info("Callbacks registados com sucesso.")
    except Exception as e:
        logger.exception("Erro ao registar callbacks.")
from forms import formularioPre, formularioPos, formulariosAdmin
from utils.logger import logger

# Função que devolve o layout com base na rota atual
def get_layout(pathname, user_id):
    logger.debug(f"[Router] Pedido de layout para rota: {pathname}")
    
    if pathname == "/forms/formularioPre":
        logger.info("A carregar layout: formulário de pré-avaliação")
        return formularioPre.layout(user_id)
    
    elif pathname == "/forms/formularioPos":
        logger.info("A carregar layout: formulário de pós-avaliação")
        return formularioPos.layout(user_id)
    
    elif pathname == "/forms/formularioAdmin":
        logger.info("A carregar layout: administração de formulários")
        return formulariosAdmin.layout()
    
    logger.warning(f"[Router] Rota não reconhecida: {pathname}")
    return None

# Registo dos callbacks de cada componente
def register_callbacks(app):
    logger.info("A registar callbacks dos formulários...")
    
    try:
        formularioPre.register_callbacks(app)
        formularioPos.register_callbacks(app)
        formulariosAdmin.register_callbacks(app)
        logger.info("Callbacks registados com sucesso.")
    except Exception as e:
        logger.exception("Erro ao registar callbacks.")