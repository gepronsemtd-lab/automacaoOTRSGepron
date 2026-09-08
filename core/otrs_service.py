import requests
import re
import logging
import time
import pandas as pd
from io import BytesIO
from .config import OTRS_URL_BASE, OTRS_USER, OTRS_PASS

logger = logging.getLogger(__name__)

STATUS_CODES_TRANSITORIOS = {429, 500, 502, 503, 504}


def _post_com_retry(session, *, url, tentativas=5, espera_inicial=5, **kwargs):
    ultima_excecao = None

    for tentativa in range(1, tentativas + 1):
        try:
            resposta = session.post(url, **kwargs)
            resposta.raise_for_status()
            return resposta
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None

            if status_code not in STATUS_CODES_TRANSITORIOS:
                raise

            ultima_excecao = exc
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            ultima_excecao = exc

        if tentativa == tentativas:
            break

        espera = espera_inicial * (2 ** (tentativa - 1))
        logger.warning(
            "Falha temporaria ao acessar OTRS. Tentativa %s/%s falhou: %s. "
            "Nova tentativa em %ss.",
            tentativa,
            tentativas,
            ultima_excecao,
            espera,
        )
        time.sleep(espera)

    raise ultima_excecao


def extrair_dados_otrs(data_filtro: str) -> pd.DataFrame:
    if not all([OTRS_USER, OTRS_PASS]):
        raise RuntimeError("Erro: OTRS_USER e OTRS_PASS precisam estar definidos.")

    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # 1. Login
    payload_login = {
        'Action': 'Login', 'RequestedURL': '', 'Lang': 'pt_BR',
        'TimeZoneOffset': '180', 'User': OTRS_USER, 'Password': OTRS_PASS
    }
    
    res_login_page = _post_com_retry(
        session,
        url=OTRS_URL_BASE,
        data=payload_login,
        headers=headers,
        timeout=30,
    )

    match = re.search(r'ChallengeToken=([^"&;]+)', res_login_page.text)
    if not match:
        raise ValueError('ChallengeToken não encontrado na resposta de login.')

    # 2. Requisição do SQL
    sql_query = f"""
    SELECT
        t.id AS ChamadoID, t.tn AS NumeroChamado, tt.name AS Tipo, t.title AS Titulo,
        t.create_time AS DataCriacao, t.change_time AS DataModificacao, ts.name AS Estado,
        q.name AS Fila, t.customer_id AS ClienteID, t.customer_user_id AS UsuarioCliente,
        u.first_name || ' ' || u.last_name AS ProprietarioNome, tp.name AS Prioridade, s.name AS Servico
    FROM ticket t
    LEFT JOIN ticket_type tt ON t.type_id = tt.id
    LEFT JOIN ticket_state ts ON t.ticket_state_id = ts.id
    LEFT JOIN queue q ON t.queue_id = q.id
    LEFT JOIN users u ON t.user_id = u.id
    LEFT JOIN ticket_priority tp ON t.ticket_priority_id = tp.id
    LEFT JOIN service s ON t.service_id = s.id
    WHERE t.create_time >= '{data_filtro} 00:00:00'
      AND q.name IN ('SESUITE-N1', 'SESUITE-N2', 'SESUITE-N3')
    ORDER BY t.create_time DESC
    """

    res_csv = _post_com_retry(
        session,
        url=OTRS_URL_BASE,
        data={
            'Action': 'AdminSelectBox', 'Subaction': 'Select',
            'ChallengeToken': match.group(1), 'SQL': sql_query,
            'Max': '', 'ResultFormat': 'CSV'
        },
        headers=headers,
        timeout=60,
    )

    if 'csv' not in res_csv.headers.get('Content-Type', '').lower():
        raise ValueError('A resposta da extração não é um arquivo CSV válido.')

    return pd.read_csv(BytesIO(res_csv.content))
