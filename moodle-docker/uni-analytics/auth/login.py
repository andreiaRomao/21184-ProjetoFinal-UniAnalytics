from dash import html, dcc, Input, Output, State, ctx, no_update
from auth.authentication import authenticate_user, register_user
from utils.logger import logger
from flask import session

# Layout da página de autenticação
def layout():
    return html.Div(
        className="auth-wrapper",
        children=[
            html.Div(
                className="auth-card-row",
                children=[
                    # Caixa lateral informativa
                    html.Div(
                        className="auth-info-box",
                        children=[
                            html.H2("Bem-vindo!", className="auth-info-title"),
                            html.P("Esta é a plataforma de Learning Analytics da UAb."),
                            html.P("Se nunca acedeu, deve registrar-se primeiro com um utilizador Moodle válido."),
                        ]
                    ),

                    # Formulário
                    html.Div(
                        className="auth-card",
                        children=[
                            html.H2("Autenticação", className="card-title-login"),
                            dcc.RadioItems(
                                id='auth-mode',
                                options=[
                                    {'label': 'Login', 'value': 'login'},
                                    {'label': 'Registar', 'value': 'register'}
                                ],
                                value='login',
                                className="auth-mode-toggle"
                            ),
                            html.Div([
                                html.Div([
                                    dcc.Input(id="login-email", type="email", placeholder="Email", className="input-auth"),
                                    dcc.Input(id="login-password", type="password", placeholder="Password", className="input-auth"),
                                    html.Button("Entrar", id="login-button", n_clicks=0, className="auth-button")
                                ], id="login-form", className="auth-form-line"),

                                html.Div([
                                    dcc.Input(id="register-email", type="email", placeholder="Email", className="input-auth"),
                                    dcc.Input(id="register-password", type="password", placeholder="Password", className="input-auth"),
                                    html.Button("Criar Conta", id="register-button", n_clicks=0, className="auth-button")
                                ], id="register-form", className="auth-form-line", style={"display": "none"})
                            ]),
                            html.Div(id="login-message", style={"color": "red", "margin": "10px", "textAlign": "center"}),
                            dcc.Store(id="login-state", storage_type="session")
                        ]
                    )
                ]
            )
        ]
    )


# Registo dos callbacks de autenticação
def register_callbacks(app):
    # Alterna a visibilidade entre o formulário de login e o de registo
    @app.callback(
        Output("login-form", "style"),
        Output("register-form", "style"),
        Input("auth-mode", "value")
    )
    def toggle_forms(mode):
        if mode == "login":
            return {"display": "block", "marginBottom": "30px"}, {"display": "none"}
        return {"display": "none"}, {"display": "block", "marginBottom": "30px"}

    # Callback para autenticação
    @app.callback(
        Output("login-message", "children"),
        Output("login-state", "data"),
        Input("login-button", "n_clicks"),
        Input("register-button", "n_clicks"),
        State("login-email", "value"),
        State("login-password", "value"),
        State("register-email", "value"),
        State("register-password", "value"),
        prevent_initial_call=True
    )
    def handle_auth(login_clicks, register_clicks, login_email, login_password, reg_email, reg_password):
        triggered_id = ctx.triggered_id

        def get_redirect_path(role):

            return "/home"

        if triggered_id == "login-button":
            if not login_email or not login_password:
                logger.warning("Tentativa de login com campos em branco.")
                return "Email e password obrigatórios", no_update

            user_info = authenticate_user(login_email, login_password)
            if user_info:
                session['user_id'] = user_info['moodle_user_id']
                session['role'] = user_info['mapped_role']
                logger.info(f"Login bem-sucedido para o utilizador: ID={user_info['moodle_user_id']}, Role={user_info['mapped_role']}")
                return "", {"redirect": get_redirect_path(user_info['mapped_role'])}

            logger.warning(f"Tentativa de login falhada para o utilizador: {login_email}")
            return "Credenciais inválidas", no_update

        elif triggered_id == "register-button":
            if not reg_email or not reg_password:
                logger.warning("Tentativa de registo com campos em branco.")
                return "Email e password obrigatórios", no_update

            sucesso, mensagem, user_info = register_user(reg_email, reg_password)
            if sucesso:
                session['user_id'] = user_info['moodle_user_id']
                session['role'] = user_info['mapped_role']
                logger.info(f"Utilizador registado: ID={user_info['moodle_user_id']}, Role={user_info['mapped_role']}")
                return "", {"redirect": get_redirect_path(user_info['mapped_role'])}

            logger.warning(f"Falha no registo do utilizador: {reg_email} — {mensagem}")
            return mensagem, no_update

        return no_update, no_update