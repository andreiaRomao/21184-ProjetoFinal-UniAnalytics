from forms import formularioPre, formularioPos

def get_layout(pathname):
    if pathname == "/forms/formularioPre":
        return formularioPre.layout()
    elif pathname == "/forms/formularioPos":
        return formularioPos.layout()
    return None

def register_callbacks(app):
    formularioPre.register_callbacks(app)
    formularioPos.register_callbacks(app)