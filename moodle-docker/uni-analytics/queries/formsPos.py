from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger

"""
| ID Pergunta | Texto da Pergunta                                                                          | ID Resposta | Texto da Resposta                                                                                                        |
| ----------- | ------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| 15          | Depois de teres realizado o e-fólio, como classificas a tua preparação?                    | 47          | Estava preparado/a – compreendi bem os conteúdos e senti que consegui aplicar os conhecimentos com confiança.           |
| 15          | Depois de teres realizado o e-fólio, como classificas a tua preparação?                    | 48          | Estava razoavelmente preparado/a – consegui responder, mas ainda com algumas dúvidas ou inseguranças.                   |
| 15          | Depois de teres realizado o e-fólio, como classificas a tua preparação?                    | 49          | Não estava devidamente preparado/a – percebi que ainda não dominava bem os conteúdos ou não tive tempo suficiente.     |
| 16          | Qual é a tua expectativa de desempenho neste e-fólio?                                      | 50          | Expectativa elevada – senti que correu bem e espero um resultado muito bom.                                             |
| 16          | Qual é a tua expectativa de desempenho neste e-fólio?                                      | 51          | Expectativa moderada – respondi ao essencial, mas com dúvidas ou deixando partes por fazer.                             |
| 16          | Qual é a tua expectativa de desempenho neste e-fólio?                                      | 52          | Expectativa positiva – consegui aplicar os conhecimentos e senti segurança na maioria das respostas.                    |
| 16          | Qual é a tua expectativa de desempenho neste e-fólio?                                      | 53          | Não consegui responder ou espero ter um resultado muito baixo.                                                          |
| 17          | Quanto tempo estimado dedicaste à realização do e-fólio?                                   | 54          | Entre 2h a 5h (inclusive).                                                                                               |
| 17          | Quanto tempo estimado dedicaste à realização do e-fólio?                                   | 55          | Entre 5h a 10h (inclusive).                                                                                              |
| 17          | Quanto tempo estimado dedicaste à realização do e-fólio?                                   | 56          | Mais de 10h.                                                                                                             |
| 17          | Quanto tempo estimado dedicaste à realização do e-fólio?                                   | 57          | Menos de 2h.                                                                                                             |
| 18          | Como classificas a dificuldade do e-fólio?                                                 | 58          | Exigente, achei difícil, não consegui responder e/ou senti que as atividades não me prepararam adequadamente.           |
| 18          | Como classificas a dificuldade do e-fólio?                                                 | 59          | Fácil, consegui aplicar o que estudei com confiança.                                                                    |
| 18          | Como classificas a dificuldade do e-fólio?                                                 | 60          | Moderado, consegui aplicar o que estudei, mesmo que parcialmente ou com dificuldades de execução.                       |
| 19          | Como avalias o esforço que investiste na preparação e realização deste e-fólio?           | 61          | Fiz um esforço razoável, existiram limitações profissionais/pessoais.                                                   |
| 19          | Como avalias o esforço que investiste na preparação e realização deste e-fólio?           | 62          | Não consegui dedicar o tempo ou a atenção necessária – sinto que o meu esforço ficou aquém.                             |
| 19          | Como avalias o esforço que investiste na preparação e realização deste e-fólio?           | 63          | Sinto que investi tudo o que podia – estudei com dedicação e mantive o compromisso até ao fim.                          |
| 20          | Os conteúdos e materiais disponibilizados cobriram bem os temas abordados no e-fólio?     | 64          | Não - senti que vários tópicos abordados não estavam nos materiais.                                                     |
| 20          | Os conteúdos e materiais disponibilizados cobriram bem os temas abordados no e-fólio?     | 65          | Parcialmente - cobriram o essencial, mas senti algumas lacunas.                                                         |
| 20          | Os conteúdos e materiais disponibilizados cobriram bem os temas abordados no e-fólio?     | 66          | Sim - os materiais prepararam-me para o que foi pedido.                                                                 |
| 21          | Relativamente á sessão síncrona de apoio ao e-fólio, como a avalias?                       | 67          | Foi muito útil – esclareceu dúvidas e deu boa orientação para o estudo.                                                 |
| 21          | Relativamente á sessão síncrona de apoio ao e-fólio, como a avalias?                       | 68          | Foi útil, esclareceu alguns pontos, mas deixou dúvidas importantes por esclarecer.                                      |
| 21          | Relativamente á sessão síncrona de apoio ao e-fólio, como a avalias?                       | 69          | Não existiu sessão síncrona de apoio à realização do e-fólio.                                                            |
| 21          | Relativamente á sessão síncrona de apoio ao e-fólio, como a avalias?                       | 70          | Não foi útil – os temas abordados não ajudaram, foi confusa ou houve falta de preparação.                               |
"""

from db.uniAnalytics import connect_to_uni_analytics_db
from utils.logger import logger

def pos_confianca_preparacao(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 47 THEN 'Preparado'
                    WHEN 48 THEN 'Razoavelmente preparado'
                    WHEN 49 THEN 'Não preparado'
                    ELSE 'Outro'
                END AS confianca_preparacao,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 15
              AND a.form_type = 'pos'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, confianca_preparacao
            ORDER BY e.item_id, confianca_preparacao;
        """
        logger.debug(f"[QUERY] pos_confianca_preparacao: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pos_confianca_preparacao")
        return []

def pos_expectativa_desempenho(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 50 THEN 'Expectativa elevada'
                    WHEN 51 THEN 'Expectativa moderada'
                    WHEN 52 THEN 'Expectativa positiva'
                    WHEN 53 THEN 'Expectativa muito baixa'
                    ELSE 'Outro'
                END AS expectativa_desempenho,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 16
              AND a.form_type = 'pos'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, expectativa_desempenho
            ORDER BY e.item_id, expectativa_desempenho;
        """
        logger.debug(f"[QUERY] pos_expectativa_desempenho: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pos_expectativa_desempenho")
        return []

def pos_dificuldade_efolio(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 58 THEN 'Difícil'
                    WHEN 59 THEN 'Fácil'
                    WHEN 60 THEN 'Moderado'
                    ELSE 'Outro'
                END AS dificuldade_efolio,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 18
              AND a.form_type = 'pos'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, dificuldade_efolio
            ORDER BY e.item_id, dificuldade_efolio;
        """
        logger.debug(f"[QUERY] pos_dificuldade_efolio: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pos_dificuldade_efolio")
        return []

def pos_esforco_investido(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 61 THEN 'Esforço razoável'
                    WHEN 62 THEN 'Esforço insuficiente'
                    WHEN 63 THEN 'Esforço máximo'
                    ELSE 'Outro'
                END AS esforco_investido,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 19
              AND a.form_type = 'pos'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, esforco_investido
            ORDER BY e.item_id, esforco_investido;
        """
        logger.debug(f"[QUERY] pos_esforco_investido: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pos_esforco_investido")
        return []

def pos_recursos_qualidade(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 64 THEN 'Não cobriram os tópicos'
                    WHEN 65 THEN 'Parcialmente cobriram'
                    WHEN 66 THEN 'Cobriram adequadamente'
                    ELSE 'Outro'
                END AS qualidade_recursos,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 20
              AND a.form_type = 'pos'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, qualidade_recursos
            ORDER BY e.item_id, qualidade_recursos;
        """
        logger.debug(f"[QUERY] pos_recursos_qualidade: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pos_recursos_qualidade")
        return []

def pos_sessao_sincrona_qualidade(item_id):
    try:
        conn = connect_to_uni_analytics_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                e.item_id,
                e.name AS item_name,
                CASE a.answer_id
                    WHEN 67 THEN 'Muito útil'
                    WHEN 68 THEN 'Útil, mas com lacunas'
                    WHEN 69 THEN 'Não existiu'
                    WHEN 70 THEN 'Não foi útil'
                    ELSE 'Outro'
                END AS qualidade_sessao_sincrona,
                COUNT(*) AS total_respostas
            FROM forms_student_answers a
            JOIN efolios e ON a.item_id = e.item_id
            WHERE a.question_id = 21
              AND a.form_type = 'pos'
              AND a.item_id = ?
            GROUP BY e.item_id, e.name, qualidade_sessao_sincrona
            ORDER BY e.item_id, qualidade_sessao_sincrona;
        """
        logger.debug(f"[QUERY] pos_sessao_sincrona_qualidade: {query.strip()} com item_id={item_id}")
        cursor.execute(query, (item_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.exception("[ADMIN] Erro ao listar respostas pos_sessao_sincrona_qualidade")
        return []