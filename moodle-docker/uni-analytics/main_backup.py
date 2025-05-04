import os
import mysql.connector
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html

import os
import time
import mysql.connector
from mysql.connector import Error

def connect_to_moodle_db(retries=10, delay=3):
    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "moodle"),
                password=os.getenv("DB_PASS", "moodle"),
                database=os.getenv("DB_NAME", "moodle")
            )
            if conn.is_connected():
                print("Uni Analytics ligado à base de dados Moodle.")
                return conn
        except Error as e:
            print(f"Tentativa {attempt+1} falhou: {e}")
            time.sleep(delay)
    raise Exception("Não foi possível ligar à base de dados após várias tentativas.")


def fetch_user_course_data():
    conn = connect_to_moodle_db()
    query = """
        SELECT c.fullname AS curso, COUNT(u.id) AS total_alunos
        FROM mdl_user u
        JOIN mdl_user_enrolments ue ON ue.userid = u.id
        JOIN mdl_enrol e ON e.id = ue.enrolid
        JOIN mdl_course c ON c.id = e.courseid
        GROUP BY c.fullname
        ORDER BY total_alunos DESC
        LIMIT 10;
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    conn.close()
    return df

def create_dashboard(df):
    fig = px.bar(df, x="curso", y="total_alunos", title="Total de alunos por curso")
    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.H1("Dashboard Moodle"),
        dcc.Graph(figure=fig)
    ])
    app.run(debug=True, host="0.0.0.0", port=8050)

if __name__ == "__main__":
    data = fetch_user_course_data()
    create_dashboard(data)