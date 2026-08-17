import requests
import re
import pandas as pd
import os
import unicodedata
import json
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

LOCAL_TIMEZONE = ZoneInfo("America/Fortaleza")

def normalize_column(column_name: str) -> str:
    normalized = unicodedata.normalize('NFKD', str(column_name))
    normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9_]', '', normalized.lower().replace(' ', '_'))

#Cálculo de percentual de N1,N2 e N3
def percentual(parte, total):
    return round((parte / total * 100), 1) if total else 0

def preparar_dashboard_data(df, agora_local, ano_atual, periodo_referencia):

    total_tickets = len(df)
    n1_count = len(df[df["fila"] == "SESUITE-N1"])
    n2_count = len(df[df["fila"] == "SESUITE-N2"])
    n3_count = len(df[df["fila"] == "SESUITE-N3"])

    n1_percent = percentual(n1_count, total_tickets)
    n2_percent = percentual(n2_count, total_tickets)
    n3_percent = percentual(n3_count, total_tickets)

    tipo_counts = df["tipo"].fillna("Não informado").value_counts().to_dict()
    fila_counts = df["fila"].fillna("Não informado").value_counts().to_dict()
    estado_counts = df["estado"].fillna("Não informado").value_counts().to_dict()

    top_analistas = df["proprietarionome"].fillna("Não informado").value_counts().head(10)
    top_servicos = df["servico"].fillna("Não informado").value_counts().head(10)

    meses = pd.period_range(
        start=f"{ano_atual}-01",
        end=agora_local.strftime("%Y-%m"),
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
        "updated": agora_local.strftime("%d/%m/%Y %H:%M:%S"),
        "period": periodo_referencia,
        "kpis": [
            {"label": "Total", "value": total_tickets, "color": "blue", "icon": "list-checks"},
            {"label": "N1", "value": n1_count, "color": "green", "icon": "check-circle"},
            {"label": "N2", "value": n2_count, "color": "amber", "icon": "clock"},
            {"label": "N3", "value": n3_count, "color": "red", "icon": "alert-triangle"},
        ],
        "progress": {
            "items": [
                {"label": "SESUITE-N1", "value": n1_count, "percent": n1_percent, "color": "green"},
                {"label": "SESUITE-N2", "value": n2_count, "percent": n2_percent, "color": "amber"},
                {"label": "SESUITE-N3", "value": n3_count, "percent": n3_percent, "color": "red"},
            ]
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

    return dashboard_data


def gerar_html_dashboard(dashboard_data):

    html_template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Gerencial de Volumetria OTRS</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #1677ff;
                --primary-soft: #e8f1ff;
                --bg: #f4f6f8;
                --surface: #ffffff;
                --text: #20242a;
                --muted: #626a73;
                --border: #e4e8ee;
                --shadow: 0 4px 14px rgba(31, 41, 55, 0.08);
                --green: #198f55;
                --green-soft: #e7f5ee;
                --amber: #ffb800;
                --amber-soft: #fff6df;
                --red: #e6374d;
                --red-soft: #ffe8ec;
                --cyan: #19c2dd;
                --cyan-soft: #e4faff;
                --gray: #6f7a82;
                --gray-soft: #eef0f2;
            }

            * {
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', Arial, sans-serif;
                background: var(--bg);
                margin: 0;
                color: var(--text);
            }

            button {
                font: inherit;
            }

            .topbar {
                min-height: 72px;
                padding: 16px 32px;
                background: var(--primary);
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
                border-radius: 0 0 16px 16px;
                box-shadow: var(--shadow);
            }

            .brand,
            .sync-pill,
            .panel-title,
            .tab-button {
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .brand {
                font-size: 22px;
                font-weight: 800;
            }

            .sync-pill {
                background: rgba(255, 255, 255, 0.14);
                padding: 10px 16px;
                border-radius: 999px;
                font-weight: 700;
            }

            .dashboard-shell {
                max-width: 1440px;
                margin: 0 auto;
                padding: 24px 32px 40px;
                display: flex;
                flex-direction: column;
                gap: 24px;
            }

            .section-card,
            .tabs-card,
            .panel-card,
            .kpi-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 16px;
                box-shadow: var(--shadow);
            }

            .intro-card {
                padding: 24px 28px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 20px;
            }

            .eyebrow {
                margin: 0 0 6px;
                color: var(--primary);
                font-size: 12px;
                font-weight: 800;
                text-transform: uppercase;
            }

            .intro-card h1 {
                margin: 0;
                font-size: 28px;
            }

            .subtitle {
                margin: 8px 0 0;
                color: var(--muted);
            }

            .period-pill {
                background: var(--primary-soft);
                color: var(--primary);
                padding: 10px 14px;
                border-radius: 999px;
                font-weight: 800;
                white-space: nowrap;
            }

            .tabs-card {
                padding: 10px;
                display: flex;
                gap: 8px;
            }

            .tab-button {
                border: 0;
                background: transparent;
                color: var(--primary);
                padding: 12px 20px;
                border-radius: 999px;
                font-weight: 800;
            }

            .tab-button.active {
                background: var(--primary);
                color: #ffffff;
            }

            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
                gap: 18px;
            }

            .kpi-card {
                min-height: 104px;
                padding: 20px;
                border-left-width: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .kpi-card h3 {
                margin: 0 0 8px;
                color: var(--muted);
                font-size: 13px;
                font-weight: 800;
                text-transform: uppercase;
            }

            .kpi-card p {
                margin: 0;
                font-size: 34px;
                font-weight: 800;
            }

            .kpi-icon {
                width: 58px;
                height: 58px;
                border-radius: 12px;
                display: grid;
                place-items: center;
            }

            .overview-grid,
            .chart-grid {
                display: grid;
                grid-template-columns: repeat(12, 1fr);
                gap: 24px;
            }

            .progress-panel {
                grid-column: span 4;
            }

            .chart-wide {
                grid-column: span 8;
            }

            .panel-card {
                padding: 24px;
                display: flex;
                flex-direction: column;
                gap: 18px;
            }

            .panel-title {
                font-size: 20px;
                font-weight: 800;
            }

            .panel-title svg {
                color: var(--primary);
            }

            .col-4 { grid-column: span 4; }
            .col-6 { grid-column: span 6; }
            .col-12 { grid-column: span 12; }

            .canvas-wrapper {
                position: relative;
                height: 340px;
                min-height: 0;
            }

            .progress-item {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .progress-item + .progress-item {
                margin-top: 18px;
            }

            .progress-meta {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                font-size: 14px;
            }

            .progress-meta strong,
            .progress-meta span {
                overflow-wrap: anywhere;
            }

            .progress-track {
                height: 12px;
                background: #edf0f4;
                border-radius: 999px;
                overflow: hidden;
            }

            .progress-fill {
                height: 100%;
                border-radius: inherit;
            }

            .tone-blue { border-left-color: var(--primary); }
            .tone-green { border-left-color: var(--green); }
            .tone-amber { border-left-color: var(--amber); }
            .tone-red { border-left-color: var(--red); }

            .tone-blue .kpi-icon { background: var(--primary-soft); color: var(--primary); }
            .tone-green .kpi-icon { background: var(--green-soft); color: var(--green); }
            .tone-amber .kpi-icon { background: var(--amber-soft); color: var(--amber); }
            .tone-red .kpi-icon { background: var(--red-soft); color: var(--red); }

            .progress-fill.tone-green { background: var(--green); }
            .progress-fill.tone-amber { background: var(--amber); }
            .progress-fill.tone-red { background: var(--red); }

            @media (max-width: 1024px) {
                .progress-panel,
                .chart-wide,
                .col-4,
                .col-6,
                .col-12 {
                    grid-column: span 12;
                }
            }

            @media (max-width: 768px) {
                .topbar,
                .intro-card,
                .tabs-card {
                    flex-direction: column;
                    align-items: flex-start;
                }

                .dashboard-shell {
                    padding: 16px;
                }

                .period-pill {
                    white-space: normal;
                }
            }

            @media (max-width: 520px) {
                .topbar {
                    padding: 14px 16px;
                }

                .brand {
                    font-size: 18px;
                }

                .intro-card h1 {
                    font-size: 22px;
                }

                .tab-button {
                    width: 100%;
                    justify-content: center;
                }

                .canvas-wrapper {
                    height: 280px;
                }
            }
        </style>
    </head>
    <body>
        <header class="topbar">
            <div class="brand">
                <i data-lucide="diamond"></i>
                <span>Dashboard Gerencial de Volumetria OTRS</span>
            </div>
            <div class="sync-pill">
                <i data-lucide="clock"></i>
                <span id="update-info"></span>
            </div>
        </header>

        <main class="dashboard-shell">
            <section class="section-card intro-card">
                <div>
                    <p class="eyebrow">GEPRON / SESUITE</p>
                    <h1>Volumetria de Chamados OTRS</h1>
                    <p class="subtitle">Acompanhamento gerencial dos chamados por nivel, tipo, estado, servico e analista.</p>
                </div>
                <span class="period-pill" id="period-info"></span>
            </section>

            <nav class="tabs-card">
                <button class="tab-button active" type="button">
                    <i data-lucide="chart-line"></i>
                    Visao Geral / Analytics
                </button>
                <button class="tab-button" type="button">
                    <i data-lucide="list-checks"></i>
                    Detalhamento Operacional
                </button>
            </nav>

            <section class="kpi-grid" id="kpi-container"></section>

            <section class="overview-grid">
                <article class="panel-card progress-panel">
                    <div class="panel-title">
                        <i data-lucide="rocket"></i>
                        <span>Distribuicao por Nivel</span>
                    </div>
                    <div id="progress-container"></div>
                </article>

                <article class="panel-card chart-wide">
                    <div class="panel-title">
                        <i data-lucide="activity"></i>
                        <span>Evolucao Mensal</span>
                    </div>
                    <div class="canvas-wrapper"><canvas id="chartTimeline"></canvas></div>
                </article>
            </section>

            <section class="chart-grid">
                <article class="panel-card col-4">
                    <div class="panel-title"><i data-lucide="pie-chart"></i><span>Volume por Tipo</span></div>
                    <div class="canvas-wrapper"><canvas id="chartTipos"></canvas></div>
                </article>

                <article class="panel-card col-4">
                    <div class="panel-title"><i data-lucide="layers"></i><span>Distribuicao por Fila</span></div>
                    <div class="canvas-wrapper"><canvas id="chartFilas"></canvas></div>
                </article>

                <article class="panel-card col-4">
                    <div class="panel-title"><i data-lucide="bar-chart-3"></i><span>Classificacao por Estado</span></div>
                    <div class="canvas-wrapper"><canvas id="chartEstados"></canvas></div>
                </article>

                <article class="panel-card col-6">
                    <div class="panel-title"><i data-lucide="users"></i><span>Top 10 Analistas</span></div>
                    <div class="canvas-wrapper"><canvas id="chartAnalistas"></canvas></div>
                </article>

                <article class="panel-card col-6">
                    <div class="panel-title"><i data-lucide="briefcase-business"></i><span>Top 10 Servicos</span></div>
                    <div class="canvas-wrapper"><canvas id="chartServicos"></canvas></div>
                </article>
            </section>
        </main>

        <script>
            Chart.register(ChartDataLabels);
            const data = DATA_PLACEHOLDER;

            document.getElementById("update-info").innerText = `Sincronizado: ${data.updated}`;
            document.getElementById("period-info").innerText = data.period;

            document.getElementById("kpi-container").innerHTML = data.kpis
                .map((item) => `
                    <article class="kpi-card tone-${item.color}">
                        <div>
                            <h3>${item.label}</h3>
                            <p>${item.value}</p>
                        </div>
                        <div class="kpi-icon"><i data-lucide="${item.icon}"></i></div>
                    </article>
                `)
                .join("");

            document.getElementById("progress-container").innerHTML = data.progress.items
                .map((item) => `
                    <div class="progress-item">
                        <div class="progress-meta">
                            <strong>${item.label}</strong>
                            <span>${item.percent}% (${item.value}/${data.kpis[0].value})</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-fill tone-${item.color}" style="width: ${item.percent}%"></div>
                        </div>
                    </div>
                `)
                .join("");

            const palette = ["#1677ff", "#198f55", "#ffb800", "#e6374d", "#19c2dd", "#6f7a82", "#111827"];

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
                },
                scales: {
                    x: {
                        ticks: { color: "#626a73", font: { family: "Inter" } },
                        grid: { color: "#e4e8ee" }
                    },
                    y: {
                        ticks: { color: "#626a73", font: { family: "Inter" } },
                        grid: { color: "#e4e8ee" }
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
                        { label: "Total", data: data.charts.timeline.total, borderColor: "#1677ff", backgroundColor: "#1677ff", tension: 0.2 },
                        { label: "N1", data: data.charts.timeline.n1, borderColor: "#198f55", backgroundColor: "#198f55", tension: 0.2 },
                        { label: "N2", data: data.charts.timeline.n2, borderColor: "#ffb800", backgroundColor: "#ffb800", tension: 0.2 },
                        { label: "N3", data: data.charts.timeline.n3, borderColor: "#e6374d", backgroundColor: "#e6374d", tension: 0.2 }
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
                type: "doughnut",
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
                    datasets: [{ label: "Qtd", data: data.charts.estados.values, backgroundColor: palette, borderRadius: 8 }]
                },
                options: commonOptions
            });

            new Chart(document.getElementById("chartAnalistas"), {
                type: "bar",
                data: {
                    labels: data.charts.analistas.labels,
                    datasets: [{ label: "Atendimentos", data: data.charts.analistas.values, backgroundColor: "#8b5cf6", borderRadius: 8 }]
                },
                options: horizontalOptions
            });

            new Chart(document.getElementById("chartServicos"), {
                type: "bar",
                data: {
                    labels: data.charts.servicos.labels,
                    datasets: [{ label: "Qtd", data: data.charts.servicos.values, backgroundColor: "#1a1f36", borderRadius: 8 }]
                },
                options: horizontalOptions
            });

            lucide.createIcons();

        </script>
    </body>
    </html>
    """.replace(
        "DATA_PLACEHOLDER",
        json.dumps(dashboard_data, ensure_ascii=False),
    )

    return html_template


def salvar_dashboard(html):
    os.makedirs("dist", exist_ok=True)

    with open("dist/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Dashboard gerado em dist/index.html")

def executar_processamento_otrs():
    # 1. Configuração de Credenciais via Variáveis de Ambiente
    user = os.getenv('OTRS_USER')
    passwd = os.getenv('OTRS_PASS')

    # 2. Cálculo Dinâmico para Início do Ano Atual
    agora_local = datetime.now(LOCAL_TIMEZONE)
    ano_atual = agora_local.year
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


    df = pd.read_csv(BytesIO(res_csv.content))
    df.rename(columns={col: normalize_column(col) for col in df.columns}, inplace=True)
    print('Colunas carregadas:', df.columns.tolist())

    if 'datacriacao' not in df.columns:
        raise KeyError('A coluna datacriacao não foi encontrada no arquivo CSV gerado.')

    df['datacriacao'] = pd.to_datetime(df['datacriacao'])

    dashboard_data = preparar_dashboard_data(df, agora_local, ano_atual, periodo_referencia)
    html = gerar_html_dashboard(dashboard_data)
    salvar_dashboard(html)


if __name__ == "__main__":
    executar_processamento_otrs()
