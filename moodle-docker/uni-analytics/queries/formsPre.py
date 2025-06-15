from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger

"""
| ID Pergunta | Texto da Pergunta                                                                            | ID Resposta | Texto da Resposta                                                                                                       |
| ----------- | -------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------- |
| 10          | Como te sentes em relação à tua preparação para o e-fólio?                                   | 27          | Ainda me sinto perdido/a - Não tive tempo para estudar ou ainda não entendi bem a matéria.                              |
| 10          | Como te sentes em relação à tua preparação para o e-fólio?                                   | 28          | Estou a meio - Já comecei a estudar, mas ainda tenho dúvidas ou falta terminar a preparação.                            |
| 10          | Como te sentes em relação à tua preparação para o e-fólio?                                   | 29          | Sinto-me preparado/a - Estudei bem, percebo os conteúdos e estou confiante para realizar o e-fólio.                     |
| 11          | Aproximadamente, quantas horas no total estimas ter dedicado à preparação para este e-fólio? | 30          | Entre 10 e 20 horas (inclusive).                                                                                        |
| 11          | Aproximadamente, quantas horas no total estimas ter dedicado à preparação para este e-fólio? | 31          | Entre 20 e 40 horas (inclusive).                                                                                        |
| 11          | Aproximadamente, quantas horas no total estimas ter dedicado à preparação para este e-fólio? | 32          | Entre 5 e 10 horas (inclusive).                                                                                         |
| 11          | Aproximadamente, quantas horas no total estimas ter dedicado à preparação para este e-fólio? | 33          | Mais de 40 horas.                                                                                                       |
| 11          | Aproximadamente, quantas horas no total estimas ter dedicado à preparação para este e-fólio? | 34          | Menos de 5 horas.                                                                                                       |
| 12          | As atividades formativas ajudaram-te a preparar o e-fólio?                                   | 35          | Efetuei, mas a correção/resolução não ajudou a perceber os erros ou a matéria.                                          |
| 12          | As atividades formativas ajudaram-te a preparar o e-fólio?                                   | 36          | Efetuei, mas estavam desatualizadas ou não se relacionavam bem com o conteúdo atual.                                    |
| 12          | As atividades formativas ajudaram-te a preparar o e-fólio?                                   | 37          | Foram bem construídas, claras e ajudaram bastante na minha preparação.                                                  |
| 12          | As atividades formativas ajudaram-te a preparar o e-fólio?                                   | 38          | Foram úteis, mas encontrei lacunas nalguns temas ou explicações mais detalhadas.                                        |
| 12          | As atividades formativas ajudaram-te a preparar o e-fólio?                                   | 39          | Não efetuei ou não encontrei atividades específicas.                                                                    |
| 13          | Os materiais de apoio (PDFs, vídeos, links, etc.) foram úteis para a tua preparação?         | 40          | Não cheguei a utilizar os materiais ou não os encontrei.                                                                |
| 13          | Os materiais de apoio (PDFs, vídeos, links, etc.) foram úteis para a tua preparação?         | 41          | Os materiais ajudam em alguns pontos, mas podiam estar mais organizados ou mais completos.                              |
| 13          | Os materiais de apoio (PDFs, vídeos, links, etc.) foram úteis para a tua preparação?         | 42          | Os materiais estavam bem estruturados e foram úteis para compreender os conteúdos.                                      |
| 13          | Os materiais de apoio (PDFs, vídeos, links, etc.) foram úteis para a tua preparação?         | 43          | Utilizei os materiais, mas senti que eram pouco claros, desatualizados ou não ajudaram muito.                           |
| 14          | Foi fácil encontrar e aceder aos recursos e atividades no Moodle?                            | 44          | A navegação foi simples e os conteúdos estavam bem organizados e acessíveis.                                            |
| 14          | Foi fácil encontrar e aceder aos recursos e atividades no Moodle?                            | 45          | Consegui encontrar o essencial, mas a estrutura podia ser mais clara e intuitiva.                                       |
| 14          | Foi fácil encontrar e aceder aos recursos e atividades no Moodle?                            | 46          | Tive bastante dificuldade em localizar os conteúdos – a estrutura não era clara e/ou a navegação parecia desorganizada. |
"""

def pre_confianca_preparacao(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 27 THEN 'Não preparado'
                    WHEN 28 THEN 'Parcialmente preparado'
                    WHEN 29 THEN 'Preparado'
                    ELSE 'Outro'
                END AS categoria_preparacao,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 10
              AND a.form_type = 'pre'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, categoria_preparacao
            ORDER BY e.item_id, categoria_preparacao;
        """
        logger.debug(f"[QUERY] pre_confianca_preparacao: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pre_preparacao")
        return []

def pre_horas_preparacao(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 30 THEN '10 a 20h'
                    WHEN 31 THEN '20 a 40h'
                    WHEN 32 THEN '5 a 10h'
                    WHEN 33 THEN '> 40h'
                    WHEN 34 THEN '< 5h'
                    ELSE 'Outro'
                END AS horas_preparacao,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 11
              AND a.form_type = 'pre'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, horas_preparacao
            ORDER BY e.item_id, horas_preparacao;
        """
        logger.debug(f"[QUERY] pre_horas_preparacao: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pre_horas_preparacao")
        return []

def pre_atividades_utilidade(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 35 THEN 'Parcialmente úteis - correção'
                    WHEN 36 THEN 'Parcialmente úteis - desatualizadas'
                    WHEN 37 THEN 'Muito úteis'
                    WHEN 38 THEN 'Parcialmente úteis - lacunas'
                    WHEN 39 THEN 'Não realizou'
                    ELSE 'Outro'
                END AS qualidade_atividades,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 12
              AND a.form_type = 'pre'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, qualidade_atividades
            ORDER BY e.item_id, qualidade_atividades;
        """
        logger.debug(f"[QUERY] pre_atividades_utilidade: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pre_atividades_qualidade")
        return []

def pre_recursos_utilidade(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 40 THEN 'Não utilizados'
                    WHEN 41 THEN 'Parcialmente úteis - lacunas'
                    WHEN 42 THEN 'Muito úteis'
                    WHEN 43 THEN 'Pouco úteis - Necessitam revisao'
                    ELSE 'Outro'
                END AS utilidade_recursos,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 13
              AND a.form_type = 'pre'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, utilidade_recursos
            ORDER BY e.item_id, utilidade_recursos;
        """
        logger.debug(f"[QUERY] pre_recursos_utilidade: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pre_recursos_utilidade")
        return []

def pre_recursos_acessibilidade(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 44 THEN 'Acessíveis e bem organizados'
                    WHEN 45 THEN 'Acessíveis, mas estrutura confusa'
                    WHEN 46 THEN 'Pouco acessíveis e desorganizados'
                    ELSE 'Outro'
                END AS acessibilidade_recursos,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 14
              AND a.form_type = 'pre'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, acessibilidade_recursos
            ORDER BY e.item_id, acessibilidade_recursos;
        """
        logger.debug(f"[QUERY] pre_recursos_acessibilidade: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pre_recursos_acessibilidade")
        return []
