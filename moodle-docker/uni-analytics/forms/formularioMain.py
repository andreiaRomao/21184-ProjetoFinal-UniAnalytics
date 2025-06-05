from forms import formularioPre, formularioPos , formulariosAdmin

def get_layout(pathname):
    if pathname == "/forms/formularioPre":
        return formularioPre.layout()
    elif pathname == "/forms/formularioPos":
        return formularioPos.layout()
    elif pathname == "/forms/formularioAdmin":
        return formulariosAdmin.layout()
    return None

def register_callbacks(app):
    formularioPre.register_callbacks(app)
    formularioPos.register_callbacks(app)
    formulariosAdmin.register_callbacks(app)