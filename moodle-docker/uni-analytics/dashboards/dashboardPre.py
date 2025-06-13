from dash import html, dcc, Input, Output, callback
import plotly.express as px
import pandas as pd
from datetime import datetime
import queries.queriesGeral as qg
import queries.formsPre as qp
from utils.logger import logger

def layout():
    return html.Div([
        html.H2("Grau de Confiança Pré-Efólio", className="titulo-dashboard"),
        html.Div([
            dcc.Dropdown(id="dropdown_item", placeholder="Seleciona o e-Fólio", className="dropdown-uc-selector")
        ], className="dropdown-wrapper"),
        html.Div([dcc.Graph(id="grafico_confianca_preparacao")], className="grafico-wrapper")
    ])

def register_callbacks(app):
    @app.callback(
        [Output("dropdown_item", "options"), Output("dropdown_item", "value")],
        Input("url", "pathname")
    )
    def carregar_opcoes_dropdown(_):
        try:
            logger.debug("[DASHBOARD_PRE] A carregar opções para dropdown_item")
            resultados = qg.fetch_all_efolios()
            logger.debug(f"[DASHBOARD_PRE] Resultados fetch_all_efolios: {resultados}")
            df = pd.DataFrame(resultados)
            df['start_date'] = pd.to_datetime(df['start_date'])
            df['ano_letivo'] = df['start_date'].dt.year
            ano_mais_recente = df['ano_letivo'].max()
            logger.debug(f"[DASHBOARD_PRE] Ano letivo mais recente: {ano_mais_recente}")
            df_filtrado = df[df['ano_letivo'] == ano_mais_recente]
            opcoes = [{
                "label": f"{row['name']} ({row['start_date'].strftime('%Y-%m-%d')} a {row['end_date'].strftime('%Y-%m-%d')})",
                "value": row["item_id"]
            } for _, row in df_filtrado.iterrows()]
            valor_default = opcoes[0]['value'] if opcoes else None
            logger.debug(f"[DASHBOARD_PRE] Opções filtradas: {opcoes}")
            return opcoes, valor_default
        except Exception as e:
            logger.exception("[DASHBOARD_PRE] Erro ao carregar opções para dropdown")
            return [], None

    @app.callback(
        Output("grafico_confianca_preparacao", "figure"),
        Input("dropdown_item", "value")
    )
    def atualizar_grafico(item_id):
        from queries.formsPre import pre_confianca_preparacao  # import local para evitar erro circular
        dados = pre_confianca_preparacao(item_id)
        df = pd.DataFrame(dados, columns=["item_id", "item_name", "categoria_preparacao", "total_respostas"])
        fig = px.pie(df, names="categoria_preparacao", values="total_respostas", hole=0.4,
                     color_discrete_sequence=["#f08080", "#ffd700", "#90ee90"])
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20),
                          paper_bgcolor="#f4faf4", plot_bgcolor="#f4faf4", font=dict(color="#2c3e50"))
        return fig