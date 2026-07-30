import requests
import re
import pandas as pd
import os
import unicodedata
import json
from io import BytesIO
from datetime import datetime

def executar_processamento_otrs():
    # 1. Configuração de Credenciais via Variáveis de Ambiente
    user = os.getenv('OTRS_USER')
    passwd = os.getenv('OTRS_PASS')

    # 2. Cálculo Dinâmico para Início do Ano Atual
    ano_atual = datetime.now().year
    data_filtro = f"{ano_atual}-01-01"
    periodo_referencia = f"Jan/{ano_atual} até o presente"

    print(f"Iniciando processamento para o período acumulado desde: {data_filtro}")

    # 3. Extração de Dados (OTRS)
    session = requests.Session()
    url_base = "https://atendimento.sead.pb.gov.br/otrs/index.pl"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }

    if not all([user, passwd]):
        raise RuntimeError("Erro: OTRS_USER e OTRS_PASS precisam estar definidos.")

    try:
        # Login no mesmo fluxo que funcionou no Colab
        payload_login = {
            'Action': 'Login',
            'RequestedURL': '',
            'Lang': 'pt_BR',
            'TimeZoneOffset': '180',
            'User': user,
            'Password': passwd
        }
        res_login_page = session.post(url_base, data=payload_login, headers=headers, timeout=30)
        res_login_page.raise_for_status()

        match = re.search(r'ChallengeToken=([^"&;]+)', res_login_page.text)
        if not match:
            print('Erro: ChallengeToken não encontrado na resposta de login.')
            print('Status Code:', res_login_page.status_code)
            print('Parte do conteúdo retornado:', res_login_page.text[:1200])
            return

        challenge_token = match.group(1)

        sql_query = f"""
        SELECT
            t.id AS ChamadoID,
            t.tn AS NumeroChamado,
            tt.name AS Tipo,
            t.title AS Titulo,
            t.create_time AS DataCriacao,
            t.change_time AS DataModificacao,
            ts.name AS Estado,
            q.name AS Fila,
            t.customer_id AS ClienteID,
            t.customer_user_id AS UsuarioCliente,
            u.first_name || ' ' || u.last_name AS ProprietarioNome,
            tp.name AS Prioridade,
            s.name AS Servico
        FROM ticket t
        LEFT JOIN ticket_type tt ON t.type_id = tt.id
        LEFT JOIN ticket_state ts ON t.ticket_state_id = ts.id
        LEFT JOIN queue q ON t.queue_id = q.id
        LEFT JOIN users u ON t.user_id = u.id
        LEFT JOIN ticket_priority tp ON t.ticket_priority_id = tp.id
        LEFT JOIN service s ON t.service_id = s.id
        WHERE
            t.create_time >= '{data_filtro} 00:00:00'
            AND q.name IN ('SESUITE-N1', 'SESUITE-N2', 'SESUITE-N3')
        ORDER BY t.create_time DESC
        """

        res_csv = session.post(url_base, data={
            'Action': 'AdminSelectBox',
            'Subaction': 'Select',
            'ChallengeToken': challenge_token,
            'SQL': sql_query,
            'Max': '',
            'ResultFormat': 'CSV'
        }, headers=headers, timeout=60)
        res_csv.raise_for_status()

        content_type = res_csv.headers.get('Content-Type', '')
        if 'csv' not in content_type.lower():
            print('A resposta não parece ser CSV. Content-Type:', content_type)
            print('Parte do conteúdo retornado:', res_csv.text[:1200])
            return

        print(f"Dados acumulados de {ano_atual} extraídos com sucesso.")

    except Exception as e:
        print(f"Erro na extração: {e}")
        return

    # 4. Processamento e geração do dashboard HTML
    def normalize_column(column_name: str) -> str:
        normalized = unicodedata.normalize('NFKD', str(column_name))
        normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
        return re.sub(r'[^a-z0-9_]', '', normalized.lower().replace(' ', '_'))

    df = pd.read_csv(BytesIO(res_csv.content))
    df.rename(columns={col: normalize_column(col) for col in df.columns}, inplace=True)
    print('Colunas carregadas:', df.columns.tolist())

    if 'datacriacao' not in df.columns:
        raise KeyError('A coluna datacriacao não foi encontrada no arquivo CSV gerado.')

    df['datacriacao'] = pd.to_datetime(df['datacriacao'])

    total_tickets = len(df)
    n1_count = len(df[df["fila"] == "SESUITE-N1"])
    n2_count = len(df[df["fila"] == "SESUITE-N2"])
    n3_count = len(df[df["fila"] == "SESUITE-N3"])

    tipo_counts = df["tipo"].fillna("Não informado").value_counts().to_dict()
    fila_counts = df["fila"].fillna("Não informado").value_counts().to_dict()
    estado_counts = df["estado"].fillna("Não informado").value_counts().to_dict()

    top_analistas = df["proprietarionome"].fillna("Não informado").value_counts().head(10)
    top_servicos = df["servico"].fillna("Não informado").value_counts().head(10)

    meses = pd.period_range(
        start=f"{ano_atual}-01",
        end=datetime.now().strftime("%Y-%m"),
        freq="M",
    )

    labels_meses = [mes.strftime("%b/%Y") for mes in meses]
    indice_meses = [mes.strftime("%Y-%m") for mes in meses]

    def serie_mensal(dataframe):
        if dataframe.empty:
            return [0 for _ in indice_meses]

        serie = (
            dataframe.assign(mes=dataframe["datacriacao"].dt.strftime("%Y-%m"))
            .groupby("mes")
            .size()
            .reindex(indice_meses, fill_value=0)
        )
        return serie.astype(int).tolist()

    dashboard_data = {
        "updated": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "period": periodo_referencia,
        "kpis": {
            "Total": total_tickets,
            "N1": n1_count,
            "N2": n2_count,
            "N3": n3_count,
            "Taxa N1": f"{(n1_count / total_tickets * 100):.1f}%" if total_tickets else "0%",
        },
        "charts": {
            "tipos": {
                "labels": list(tipo_counts.keys()),
                "values": list(tipo_counts.values()),
            },
            "filas": {
                "labels": list(fila_counts.keys()),
                "values": list(fila_counts.values()),
            },
            "estados": {
                "labels": list(estado_counts.keys()),
                "values": list(estado_counts.values()),
            },
            "analistas": {
                "labels": top_analistas.index.tolist(),
                "values": top_analistas.astype(int).tolist(),
            },
            "servicos": {
                "labels": [
                    str(servico)[:45] + "..." if len(str(servico)) > 45 else str(servico)
                    for servico in top_servicos.index.tolist()
                ],
                "values": top_servicos.astype(int).tolist(),
            },
            "timeline": {
                "labels": labels_meses,
                "total": serie_mensal(df),
                "n1": serie_mensal(df[df["fila"] == "SESUITE-N1"]),
                "n2": serie_mensal(df[df["fila"] == "SESUITE-N2"]),
                "n3": serie_mensal(df[df["fila"] == "SESUITE-N3"]),
            },
        },
    }

    html_template = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard OTRS SESUITE</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', Arial, sans-serif;
            background-color: #f4f6f8;
            margin: 0;
            padding: 20px;
            color: #1a1f36;
        }

        .dashboard-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .header-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 16px;
            margin-bottom: 5px;
        }

        .header-title {
            font-size: 22px;
            font-weight: 700;
        }

        .last-update {
            font-size: 12px;
            color: #697386;
            font-style: italic;
            text-align: right;
        }

        .kpi-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 20px;
        }

        .kpi-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
        }

        .kpi-card h3 {
            margin: 0;
            font-size: 13px;
            color: #697386;
            text-transform: uppercase;
        }

        .kpi-card p {
            margin: 10px 0 0;
            font-size: 26px;
            font-weight: 700;
            color: #056cf2;
        }

        .chart-grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
        }

        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
        }

        .card-title {
            font-weight: 600;
            font-size: 15px;
            margin-bottom: 12px;
            color: #3c4257;
        }

        .col-4 { grid-column: span 4; }
        .col-6 { grid-column: span 6; }
        .col-12 { grid-column: span 12; }

        .canvas-wrapper {
            position: relative;
            min-height: 0;
            height: 350px;
        }

        @media (max-width: 900px) {
            body { padding: 14px; }
            .header-row {
                flex-direction: column;
                align-items: flex-start;
            }
            .last-update { text-align: left; }
            .col-4,
            .col-6 {
                grid-column: span 12;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header-row">
            <div class="header-title">Dashboard SESUITE</div>
            <div class="last-update" id="update-info"></div>
        </div>

        <div class="kpi-row" id="kpi-container"></div>

        <div class="chart-grid">
            <div class="card col-12">
                <div class="card-title">Evolução Mensal: Total vs N1 vs N2 vs N3</div>
                <div class="canvas-wrapper"><canvas id="chartTimeline"></canvas></div>
            </div>

            <div class="card col-4">
                <div class="card-title">Volume por Tipo</div>
                <div class="canvas-wrapper"><canvas id="chartTipos"></canvas></div>
            </div>

            <div class="card col-4">
                <div class="card-title">Distribuição por Fila</div>
                <div class="canvas-wrapper"><canvas id="chartFilas"></canvas></div>
            </div>

            <div class="card col-4">
                <div class="card-title">Classificação por Estado</div>
                <div class="canvas-wrapper"><canvas id="chartEstados"></canvas></div>
            </div>

            <div class="card col-6">
                <div class="card-title">Top 10 Analistas</div>
                <div class="canvas-wrapper"><canvas id="chartAnalistas"></canvas></div>
            </div>

            <div class="card col-6">
                <div class="card-title">Top 10 Serviços</div>
                <div class="canvas-wrapper"><canvas id="chartServicos"></canvas></div>
            </div>
        </div>
    </div>

    <script>
        Chart.register(ChartDataLabels);
        const data = DATA_PLACEHOLDER;

        document.getElementById("update-info").innerText =
            `Período: ${data.period} | Última atualização: ${data.updated}`;

        document.getElementById("kpi-container").innerHTML = Object.entries(data.kpis)
            .map(([key, val]) => `<div class="kpi-card"><h3>${key}</h3><p>${val}</p></div>`)
            .join("");

        const palette = ["#056cf2", "#ff5f52", "#ffbd45", "#4ade80", "#8b5cf6", "#1a1f36", "#38bdf8", "#f97316"];

        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 12, font: { size: 11 } }
                },
                datalabels: {
                    color: "#444",
                    font: { weight: "bold", size: 10 },
                    anchor: "end",
                    align: "top",
                    formatter: (value) => value > 0 ? value : ""
                }
            }
        };

        const horizontalOptions = {
            ...commonOptions,
            indexAxis: "y",
            layout: { padding: { right: 40 } },
            plugins: {
                ...commonOptions.plugins,
                datalabels: {
                    color: "#1a1f36",
                    font: { weight: "bold", size: 11 },
                    anchor: "end",
                    align: "right",
                    display: true,
                    formatter: (value) => value
                }
            }
        };

        new Chart(document.getElementById("chartTimeline"), {
            type: "line",
            data: {
                labels: data.charts.timeline.labels,
                datasets: [
                    { label: "Total", data: data.charts.timeline.total, borderColor: "#056cf2", backgroundColor: "#056cf2", tension: 0.2 },
                    { label: "N1", data: data.charts.timeline.n1, borderColor: "#4ade80", backgroundColor: "#4ade80", tension: 0.2 },
                    { label: "N2", data: data.charts.timeline.n2, borderColor: "#ffbd45", backgroundColor: "#ffbd45", tension: 0.2 },
                    { label: "N3", data: data.charts.timeline.n3, borderColor: "#ff5f52", backgroundColor: "#ff5f52", tension: 0.2 }
                ]
            },
            options: commonOptions
        });

        new Chart(document.getElementById("chartTipos"), {
            type: "doughnut",
            data: {
                labels: data.charts.tipos.labels,
                datasets: [{ data: data.charts.tipos.values, backgroundColor: palette }]
            },
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    datalabels: { color: "#fff", formatter: (value) => value > 0 ? value : "" }
                }
            }
        });

        new Chart(document.getElementById("chartFilas"), {
            type: "pie",
            data: {
                labels: data.charts.filas.labels,
                datasets: [{ data: data.charts.filas.values, backgroundColor: ["#4ade80", "#ffbd45", "#ff5f52"] }]
            },
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    datalabels: { color: "#fff", formatter: (value) => value > 0 ? value : "" }
                }
            }
        });

        new Chart(document.getElementById("chartEstados"), {
            type: "bar",
            data: {
                labels: data.charts.estados.labels,
                datasets: [{ label: "Qtd", data: data.charts.estados.values, backgroundColor: palette }]
            },
            options: commonOptions
        });

        new Chart(document.getElementById("chartAnalistas"), {
            type: "bar",
            data: {
                labels: data.charts.analistas.labels,
                datasets: [{ label: "Atendimentos", data: data.charts.analistas.values, backgroundColor: "#8b5cf6" }]
            },
            options: horizontalOptions
        });

        new Chart(document.getElementById("chartServicos"), {
            type: "bar",
            data: {
                labels: data.charts.servicos.labels,
                datasets: [{ label: "Qtd", data: data.charts.servicos.values, backgroundColor: "#1a1f36" }]
            },
            options: horizontalOptions
        });
    </script>
</body>
</html>
""".replace(
    "DATA_PLACEHOLDER",
    json.dumps(dashboard_data, ensure_ascii=False),
)

    os.makedirs("dist", exist_ok=True)

    with open("dist/index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    print("Dashboard gerado em dist/index.html")


if __name__ == "__main__":
    executar_processamento_otrs()
