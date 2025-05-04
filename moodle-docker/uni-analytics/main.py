from queries.geral import fetch_user_course_data
from dashboards.geral import create_dashboard

if __name__ == "__main__":
    data = fetch_user_course_data()
    create_dashboard(data)
