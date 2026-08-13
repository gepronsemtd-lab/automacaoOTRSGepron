# Guia Passo a Passo: GEPR-SES-02.3

Este guia explica, em ordem, o que modificar manualmente para atualizar a Dashboard de Volumetria OTRS sem perder a versao atual.

Projeto:

```text
/Users/alinesilva/Desktop/GEPRON/projects/automacaoOTRSGepron/automacaoOTRSGepron
```

Arquivo que sera alterado:

```text
main.py
```

Arquivo que sera criado:

```text
DASHBOARD_STYLE_GUIDE.md
```

Importante: nao edite `dist/index.html` manualmente. Esse arquivo deve ser gerado pela execucao de `python main.py`.

## 0. Preparar Git de Forma Reversivel

Esta parte cria um ponto de retorno e uma branch separada para a nova dashboard.

### 0.1. Entrar na pasta certa

Execute:

```bash
cd /Users/alinesilva/Desktop/GEPRON/projects/automacaoOTRSGepron/automacaoOTRSGepron
```

### 0.2. Confirmar estado atual

Execute:

```bash
git status
```

O esperado e estar em:

```text
main
```

Se aparecer apenas `DASHBOARD_REDESIGN_GUIDE.md` como arquivo novo, tudo bem.

### 0.3. Garantir que a `main` esta atualizada

Execute:

```bash
git checkout main
git pull --ff-only origin main
```

### 0.4. Criar tag com a versao atual

Execute:

```bash
git tag -a gep-ses-02-3-baseline -m "Baseline antes do redesign da dashboard OTRS"
git push origin gep-ses-02-3-baseline
```

Essa tag guarda a versao atual do site antes do redesign.

### 0.5. Criar branch para implementar a nova dashboard

Execute:

```bash
git checkout -b feature/gepr-ses-02-3-dashboard-layout
```

Checkpoint:

```bash
git status --short --branch
```

O esperado:

```text
## feature/gepr-ses-02-3-dashboard-layout
```

## 1. Refatorar o `main.py` Antes do Redesign

Objetivo: separar processamento de dados, template HTML e escrita do arquivo. Isso deixa o codigo mais facil de alterar e revisar.

Hoje o `main.py` mistura tudo dentro de `executar_processamento_otrs()`. Antes de mexer no visual, reorganize em funcoes.

## 1.1. Localizar o bloco grande atual

No `main.py`, procure este comentario:

```python
# 4. Processamento e geração do dashboard HTML
```

A partir desse ponto existe um bloco grande que faz tudo:

- declara `normalize_column`;
- le o CSV;
- calcula KPIs;
- monta `dashboard_data`;
- cria `html_template`;
- escreve `dist/index.html`.

Esse e o bloco que sera reorganizado.

## 1.2. Mover `normalize_column` para fora da funcao principal

Localize dentro de `executar_processamento_otrs()`:

```python
def normalize_column(column_name: str) -> str:
    normalized = unicodedata.normalize('NFKD', str(column_name))
    normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9_]', '', normalized.lower().replace(' ', '_'))
```

Faca:

1. Recorte esse bloco.
2. Cole logo abaixo desta linha, no topo do arquivo:

```python
LOCAL_TIMEZONE = ZoneInfo("America/Fortaleza")
```

Resultado esperado:

```python
LOCAL_TIMEZONE = ZoneInfo("America/Fortaleza")

def normalize_column(column_name: str) -> str:
    normalized = unicodedata.normalize('NFKD', str(column_name))
    normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9_]', '', normalized.lower().replace(' ', '_'))

def executar_processamento_otrs():
    ...
```

Remova a copia antiga de `normalize_column` de dentro de `executar_processamento_otrs()`.

## 1.3. Criar a funcao `percentual`

Logo abaixo de `normalize_column`, adicione:

```python
def percentual(parte, total):
    return round((parte / total * 100), 1) if total else 0
```

Essa funcao sera usada para calcular o percentual de N1, N2 e N3.

## 1.4. Criar a funcao `preparar_dashboard_data`

Neste passo voce vai mexer em dois lugares:

1. Criar uma funcao nova fora de `executar_processamento_otrs()`.
2. Remover de dentro de `executar_processamento_otrs()` o bloco que monta os dados da dashboard.

Logo abaixo de `percentual`, fora de qualquer outra funcao, crie a assinatura:

```python
def preparar_dashboard_data(df, agora_local, ano_atual, periodo_referencia):
```

Agora entre dentro da funcao `executar_processamento_otrs()` e localize esta linha:

```python
df['datacriacao'] = pd.to_datetime(df['datacriacao'])
```

Logo abaixo dela, hoje existe um bloco grande que comeca assim:

```python
total_tickets = len(df)
n1_count = len(df[df["fila"] == "SESUITE-N1"])
n2_count = len(df[df["fila"] == "SESUITE-N2"])
n3_count = len(df[df["fila"] == "SESUITE-N3"])
```

Esse bloco continua com:

- `tipo_counts`;
- `fila_counts`;
- `estado_counts`;
- `top_analistas`;
- `top_servicos`;
- `meses`;
- `labels_meses`;
- `indice_meses`;
- a funcao interna `serie_mensal`;
- a variavel `dashboard_data`.

Recorte esse bloco inteiro de dentro de `executar_processamento_otrs()`. O trecho que voce deve recortar termina no fechamento do dicionario `dashboard_data`, ou seja, depois deste padrao:

```python
dashboard_data = {
    ...
}
```

Cole esse bloco recortado dentro da funcao nova `preparar_dashboard_data(...)`, com indentacao de 4 espacos.

No final da funcao nova, logo depois do fechamento de `dashboard_data`, adicione:

```python
return dashboard_data
```

Resultado esperado da funcao nova:

```python
def preparar_dashboard_data(df, agora_local, ano_atual, periodo_referencia):
    total_tickets = len(df)
    n1_count = len(df[df["fila"] == "SESUITE-N1"])
    n2_count = len(df[df["fila"] == "SESUITE-N2"])
    n3_count = len(df[df["fila"] == "SESUITE-N3"])

    # aqui ficam tipo_counts, fila_counts, estado_counts,
    # top_analistas, top_servicos, meses, serie_mensal
    # e dashboard_data

    dashboard_data = {
        ...
    }

    return dashboard_data
```

Resultado esperado dentro de `executar_processamento_otrs()` neste momento:

```python
df['datacriacao'] = pd.to_datetime(df['datacriacao'])

# aqui ainda serao adicionadas as chamadas finais no passo 1.7
```

Ou seja: sim, voce modifica a `def executar_processamento_otrs()`. Voce tira de dentro dela o bloco de calculo/montagem dos dados e deixa esse trabalho para a nova funcao `preparar_dashboard_data(...)`.

## 1.5. Criar a funcao `gerar_html_dashboard`

Neste passo voce tambem mexe em dois lugares:

1. Criar uma funcao nova fora de `executar_processamento_otrs()`.
2. Remover de dentro de `executar_processamento_otrs()` o bloco do HTML.

Logo abaixo de `preparar_dashboard_data`, fora de qualquer outra funcao, crie:

```python
def gerar_html_dashboard(dashboard_data):
```

Entre em `executar_processamento_otrs()` e localize o bloco que hoje comeca em:

```python
html_template = """
```

Recorte todo esse bloco de dentro de `executar_processamento_otrs()`. Ele termina em:

```python
""".replace(
    "DATA_PLACEHOLDER",
    json.dumps(dashboard_data, ensure_ascii=False),
)
```

Cole esse bloco dentro da nova funcao `gerar_html_dashboard(dashboard_data)`, com indentacao de 4 espacos.

No final da nova funcao, logo depois do `.replace(...)`, adicione:

```python
return html_template
```

Resultado esperado:

```python
def gerar_html_dashboard(dashboard_data):
    html_template = """
    ...
    """.replace(
        "DATA_PLACEHOLDER",
        json.dumps(dashboard_data, ensure_ascii=False),
    )

    return html_template
```

Depois disso, a variavel `html_template` nao deve mais aparecer dentro de `executar_processamento_otrs()`.

## 1.6. Criar a funcao `salvar_dashboard`

Logo abaixo de `gerar_html_dashboard`, crie:

```python
def salvar_dashboard(html):
    os.makedirs("dist", exist_ok=True)

    with open("dist/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Dashboard gerado em dist/index.html")
```

Depois remova de `executar_processamento_otrs()` este bloco antigo:

```python
os.makedirs("dist", exist_ok=True)

with open("dist/index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("Dashboard gerado em dist/index.html")
```

## 1.7. Ajustar o final de `executar_processamento_otrs`

Agora volte para dentro de `executar_processamento_otrs()`.

Depois da refatoracao dos passos 1.4, 1.5 e 1.6, o final da funcao deve estar sem os blocos de KPI, HTML e escrita do arquivo.

Dentro de `executar_processamento_otrs()`, localize:

```python
df['datacriacao'] = pd.to_datetime(df['datacriacao'])
```

Logo abaixo dela, adicione estas tres chamadas:

```python
dashboard_data = preparar_dashboard_data(df, agora_local, ano_atual, periodo_referencia)
html = gerar_html_dashboard(dashboard_data)
salvar_dashboard(html)
```

Esse e o novo final esperado de `executar_processamento_otrs()`:

```python
df['datacriacao'] = pd.to_datetime(df['datacriacao'])

dashboard_data = preparar_dashboard_data(df, agora_local, ano_atual, periodo_referencia)
html = gerar_html_dashboard(dashboard_data)
salvar_dashboard(html)
```

Depois confira se dentro de `executar_processamento_otrs()` nao ficou nenhum destes blocos antigos:

- calculo de KPIs;
- criacao de `dashboard_data`;
- criacao de `html_template`;
- escrita de `dist/index.html`.

Checkpoint da Parte 1:

```bash
python -m py_compile main.py
```

Se nao mostrar erro, a refatoracao estrutural esta sintaticamente ok.

## 2. Alterar os Dados que Alimentam os Cards e Progresso

Objetivo: trocar os KPIs simples por KPIs com metadados visuais e criar dados de progresso por nivel.

Faca tudo desta parte dentro de:

```python
def preparar_dashboard_data(df, agora_local, ano_atual, periodo_referencia):
```

## 2.1. Adicionar percentuais de N1, N2 e N3

Localize:

```python
total_tickets = len(df)
n1_count = len(df[df["fila"] == "SESUITE-N1"])
n2_count = len(df[df["fila"] == "SESUITE-N2"])
n3_count = len(df[df["fila"] == "SESUITE-N3"])
```

Logo abaixo, adicione:

```python
n1_percent = percentual(n1_count, total_tickets)
n2_percent = percentual(n2_count, total_tickets)
n3_percent = percentual(n3_count, total_tickets)
```

## 2.2. Substituir o bloco `kpis`

Dentro de `dashboard_data`, encontre exatamente este formato antigo:

```python
"kpis": {
    "Total": total_tickets,
    "N1": n1_count,
    "N2": n2_count,
    "N3": n3_count,
    "Taxa N1": f"{(n1_count / total_tickets * 100):.1f}%" if total_tickets else "0%",
},
```

Substitua por:

```python
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
```

Remova:

- o card `"Taxa N1"`;
- qualquer calculo antigo de taxa que tenha ficado solto.

Preserve:

- `charts`;
- `tipos`;
- `filas`;
- `estados`;
- `analistas`;
- `servicos`;
- `timeline`.

Checkpoint:

```bash
python -m py_compile main.py
```

## 3. Atualizar o `<head>` do HTML

Objetivo: trocar o titulo da pagina e adicionar a biblioteca de icones usada no novo visual.

Faca dentro de:

```python
def gerar_html_dashboard(dashboard_data):
```

## 3.1. Localizar o inicio do template

Procure:

```html
<title>Dashboard OTRS SESUITE</title>
```

E este bloco:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
```

## 3.2. Substituir por

```html
<title>Dashboard Gerencial de Volumetria OTRS</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
<script src="https://unpkg.com/lucide@latest"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
```

Nao remova Chart.js nem `chartjs-plugin-datalabels`.

## 4. Substituir Todo o CSS Antigo

Objetivo: trocar o visual simples atual pelo visual parecido com o GEP-664: topo azul, fundo cinza, cards brancos, icones, abas, KPIs com borda colorida e barras de progresso.

## 4.1. Localizar o CSS antigo

Dentro do `html_template`, procure:

```html
<style>
```

Substitua tudo entre `<style>` e `</style>`.

Remova completamente estas classes antigas:

- `.dashboard-container`;
- `.header-row`;
- `.header-title`;
- `.last-update`;
- `.kpi-row`;
- `.card`;
- `.card-title`.

## 4.2. Colar o CSS novo

Use este CSS como base:

```css
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
```

Checkpoint:

- O CSS antigo nao deve mais existir.
- As classes novas devem bater com o HTML que sera criado no passo 5.

## 5. Substituir o HTML do Corpo da Pagina

Objetivo: reorganizar a dashboard na hierarquia gerencial do GEP-664.

## 5.1. Localizar o corpo antigo

Dentro de `html_template`, localize:

```html
<body>
```

Depois disso, existe hoje este bloco antigo:

```html
<div class="dashboard-container">
    ...
</div>
```

Substitua todo o conteudo entre `<body>` e antes de `<script>` pelo HTML abaixo.

## 5.2. Colar o novo corpo

```html
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
```

## 5.3. Remover o HTML antigo

Remova completamente:

- `<div class="dashboard-container">`;
- `<div class="header-row">`;
- `<div class="header-title">Dashboard SESUITE</div>`;
- `<div class="last-update" id="update-info"></div>`;
- `<div class="kpi-row" id="kpi-container"></div>`;
- todos os cards antigos com `class="card ..."` dentro do antigo `.chart-grid`.

Preserve apenas:

- os mesmos IDs dos canvas;
- o bloco `<script>` que vem depois, porque ele sera ajustado no passo 6.

## 6. Atualizar o JavaScript de Renderizacao

Objetivo: fazer o novo HTML receber dados corretamente.

## 6.1. Trocar texto de periodo e atualizacao

Localize:

```js
document.getElementById("update-info").innerText =
    `Período: ${data.period} | Última atualização: ${data.updated}`;
```

Substitua por:

```js
document.getElementById("update-info").innerText = `Sincronizado: ${data.updated}`;
document.getElementById("period-info").innerText = data.period;
```

## 6.2. Trocar renderizacao dos KPIs

Localize:

```js
document.getElementById("kpi-container").innerHTML = Object.entries(data.kpis)
    .map(([key, val]) => `<div class="kpi-card"><h3>${key}</h3><p>${val}</p></div>`)
    .join("");
```

Substitua por:

```js
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
```

## 6.3. Adicionar renderizacao do progresso

Logo depois do bloco novo dos KPIs, adicione:

```js
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
```

## 6.4. Inicializar icones Lucide

No final do `<script>`, depois da criacao de todos os graficos e antes de:

```html
</script>
```

Adicione:

```js
lucide.createIcons();
```

Checkpoint:

- Nao deve existir mais `Object.entries(data.kpis)`.
- Deve existir `period-info`.
- Deve existir `progress-container`.
- Deve existir `lucide.createIcons()`.

## 7. Ajustar Aparencia dos Graficos

Objetivo: alinhar as cores dos graficos ao novo padrao visual.

## 7.1. Trocar paleta

Localize:

```js
const palette = ["#056cf2", "#ff5f52", "#ffbd45", "#4ade80", "#8b5cf6", "#1a1f36", "#38bdf8", "#f97316"];
```

Substitua por:

```js
const palette = ["#1677ff", "#198f55", "#ffb800", "#e6374d", "#19c2dd", "#6f7a82", "#111827"];
```

## 7.2. Atualizar cores do grafico de evolucao

No grafico `chartTimeline`, troque os datasets para usar:

- Total: `#1677ff`;
- N1: `#198f55`;
- N2: `#ffb800`;
- N3: `#e6374d`.

## 7.3. Trocar fila de pizza para rosca

Localize:

```js
new Chart(document.getElementById("chartFilas"), {
    type: "pie",
```

Troque para:

```js
new Chart(document.getElementById("chartFilas"), {
    type: "doughnut",
```

## 7.4. Arredondar barras

Nos datasets dos graficos de barra, adicione:

```js
borderRadius: 8
```

Exemplo:

```js
datasets: [{ label: "Qtd", data: data.charts.estados.values, backgroundColor: palette, borderRadius: 8 }]
```

Faca isso em:

- `chartEstados`;
- `chartAnalistas`;
- `chartServicos`.

## 7.5. Ajustar `commonOptions`

Dentro de `commonOptions`, mantenha a estrutura atual, mas adicione/ajuste:

```js
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
```

Observacao: graficos `doughnut` nao usam escalas, mas Chart.js ignora isso sem quebrar na maioria dos casos. Se algum grafico de rosca apresentar erro, crie opcoes separadas para graficos sem eixo.

## 8. Criar Documentacao Visual

Crie um novo arquivo:

```text
DASHBOARD_STYLE_GUIDE.md
```

Cole:

```markdown
# Identidade Visual das Dashboards GEPRON

## Referencia

Padrao visual baseado no Dashboard Executivo da Esteira SEMTD (GEP-664).

## Tokens

- Azul principal: `#1677ff`
- Fundo: `#f4f6f8`
- Superficie: `#ffffff`
- Texto principal: `#20242a`
- Texto secundario: `#626a73`
- Verde: `#198f55`
- Amarelo: `#ffb800`
- Vermelho: `#e6374d`
- Ciano: `#19c2dd`

## Componentes

- Topbar azul com titulo branco.
- Cards brancos com `border-radius: 16px` e sombra leve.
- KPIs com borda lateral colorida e icone em bloco suave.
- Progresso com barra horizontal e percentual visivel.
- Graficos em cards brancos com titulo e icone.

## Hierarquia

1. Visao geral no topo.
2. Indicadores consolidados.
3. Progresso gerencial.
4. Graficos analiticos.
5. Detalhamento operacional.

## Responsividade

No mobile, a dashboard deve virar coluna unica, sem sobreposicao de texto e sem corte nos cards.
```

## 9. Validar Manualmente

## 9.1. Validar sintaxe Python

Execute:

```bash
python -m py_compile main.py
```

## 9.2. Gerar dashboard

Execute:

```bash
python main.py
```

Se o script depender de credenciais, confirme que `OTRS_USER` e `OTRS_PASS` estao definidos.

## 9.3. Abrir arquivo gerado

Abra:

```text
dist/index.html
```

Valide:

- desktop largo: KPIs em linha, topo azul, graficos em grid;
- tablet: cards reorganizados sem sobreposicao;
- mobile: tudo em uma coluna;
- nomes longos de analista e servico sem estourar cards;
- dataset vazio: valores `0`, barras `0%`, graficos sem quebra;
- apenas uma fila com dados: percentuais continuam corretos.

## 10. Commit e PR

Quando estiver validado:

```bash
git status
git diff
git add main.py DASHBOARD_STYLE_GUIDE.md DASHBOARD_REDESIGN_GUIDE.md
git commit -m "Redesenha dashboard de volumetria OTRS"
git push -u origin feature/gepr-ses-02-3-dashboard-layout
```

Abra PR da branch:

```text
feature/gepr-ses-02-3-dashboard-layout
```

Para:

```text
main
```

So faca merge depois da validacao visual em desktop e mobile.
