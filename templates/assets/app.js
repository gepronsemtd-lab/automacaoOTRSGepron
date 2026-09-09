const EMPTY_DASHBOARD_DATA = {
    updated: "--",
    period: "",
    kpis: [],
    progress: { items: [] },
    charts: {
        tipos: { labels: [], values: [] },
        filas: { labels: [], values: [] },
        estados: { labels: [], values: [] },
        analistas: { labels: [], values: [] },
        servicos: { labels: [], values: [] },
        riscos: { labels: [], values: [], worstCase: 0 },
        timeline: { labels: [], total: [], n1: [], n2: [], n3: [] },
    },
    records: [],
    filters: {},
};

if (window.Chart && window.ChartDataLabels) {
    Chart.register(ChartDataLabels);
}

// Lê os dados que o Python injetou no HTML
const injectedData = window.DASHBOARD_DATA;
const hasInjectedData = injectedData && typeof injectedData === "object";
const data = hasInjectedData ? injectedData : EMPTY_DASHBOARD_DATA;
const allRecords = data.records || [];
let filteredRecords = [...allRecords];

const syncButton = document.getElementById("sync-button");
const logoutButton = document.getElementById("logout-button");
const themeToggle = document.getElementById("theme-toggle");
const filterBody = document.getElementById("filter-body");
const filterToggle = document.getElementById("filter-toggle");
const resultCount = document.getElementById("result-count");
const operationsCount = document.getElementById("operations-count");
const emptyState = document.getElementById("empty-state");
const isStaticPagesHost = window.location.hostname.endsWith(".github.io");
const workflowUrl = "https://github.com/gepronsemtd-lab/automacaoOTRSGepron/actions/workflows/main.yml";

function refreshIcons() {
    if (window.lucide) {
        lucide.createIcons();
        document.documentElement.classList.add("icons-ready");
    } else {
        document.documentElement.classList.remove("icons-ready");
    }
}

function getStoredTheme() {
    try {
        return localStorage.getItem("dashboardTheme");
    } catch (error) {
        return null;
    }
}

function setStoredTheme(theme) {
    try {
        localStorage.setItem("dashboardTheme", theme);
    } catch (error) {
        // O Safari pode bloquear localStorage em arquivo local.
    }
}

function updateThemeButton() {
    if (!themeToggle) return;

    const isDark = document.documentElement.dataset.theme === "dark";
    themeToggle.title = isDark ? "Alternar para tema claro" : "Alternar para tema escuro";
    themeToggle.innerHTML = isDark
        ? '<i data-lucide="sun" data-fallback="☀"></i>'
        : '<i data-lucide="moon" data-fallback="☾"></i>';
    refreshIcons();
}

themeToggle?.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    setStoredTheme(nextTheme);
    updateThemeButton();
    renderCharts();
});

const savedTheme = getStoredTheme();
if (savedTheme) {
    document.documentElement.dataset.theme = savedTheme;
}
updateThemeButton();

syncButton?.addEventListener("click", async () => {
    if (isStaticPagesHost) {
        window.open(workflowUrl, "_blank", "noopener,noreferrer");
        return;
    }

    syncButton.disabled = true;
    syncButton.querySelector("span").innerText = "Sincronizando...";

    try {
        const response = await fetch("/sync", { method: "POST" });
        if (!response.ok) {
            let message = "Falha na sincronização";
            try {
                const payload = await response.json();
                message = payload.error || message;
            } catch (error) {
                // Mantém a mensagem padrão quando a resposta não é JSON.
            }
            throw new Error(message);
        }
        window.location.reload();
    } catch (error) {
        alert(`Não foi possível sincronizar agora. ${error.message}`);
    } finally {
        syncButton.disabled = false;
        syncButton.querySelector("span").innerText = "Sincronizar";
    }
});

logoutButton?.addEventListener("click", () => {
    window.location.href = "/logout";
});

// Preenche os textos de cabeçalho
document.getElementById("update-info").innerText = `Sincronizado: ${data.updated}`;
const periodInfo = document.getElementById("period-info");
if (periodInfo) {
    periodInfo.innerText = data.period;
}

function formatCountLabel(total) {
    if (!hasInjectedData) {
        return "Dados não carregados";
    }

    return total === 1 ? "1 chamado encontrado" : `${total} chamados encontrados`;
}

function updateResultCount(records) {
    const label = formatCountLabel(records.length);
    if (resultCount) {
        resultCount.innerText = label;
    }
    if (operationsCount) {
        operationsCount.innerText = label;
    }
}

function updateEmptyState(records) {
    if (!emptyState) return;

    emptyState.hidden = records.length > 0 && hasInjectedData;
    emptyState.querySelector("h2").innerText = hasInjectedData
        ? "Nenhum chamado encontrado"
        : "Dashboard aberto sem dados";
    emptyState.querySelector("p").innerText = hasInjectedData
        ? "Revise os filtros aplicados ou limpe a busca para voltar à visão completa."
        : "Abra o painel pelo servidor Flask ou pelo arquivo dist/index.html gerado pelo pipeline.";
}

function switchTab(tabName) {
    document.querySelectorAll(".tab-button").forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tabName);
    });

    document.querySelectorAll(".tab-panel").forEach((panel) => {
        panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });
}

document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => {
        switchTab(button.dataset.tab);
    });
});

function escapeHTML(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function fillSelect(id, values, allLabel) {
    const select = document.getElementById(id);
    if (!select) return;

    select.innerHTML = [
        `<option value="">${escapeHTML(allLabel)}</option>`,
        ...values.map((value) => `<option value="${escapeHTML(value)}">${escapeHTML(value)}</option>`)
    ].join("");
}

function countBy(records, field, limit = null) {
    const counts = records.reduce((result, item) => {
        const key = item[field] || "Não informado";
        result[key] = (result[key] || 0) + 1;
        return result;
    }, {});

    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return limit ? entries.slice(0, limit) : entries;
}

function chartFromCounts(records, field, limit = null) {
    const entries = countBy(records, field, limit);
    return {
        labels: entries.map(([label]) => label),
        values: entries.map(([, value]) => value),
    };
}

function percentualJS(parte, total) {
    return total ? Math.round((parte / total * 100) * 10) / 10 : 0;
}

function formatDateBR(value) {
    if (!value) return "Não informado";

    const date = parseDashboardDate(value);
    if (Number.isNaN(date.getTime())) {
        return String(value).slice(0, 10) || "Não informado";
    }

    return date.toLocaleDateString("pt-BR");
}

function parseDashboardDate(value) {
    return new Date(String(value).replace(" ", "T"));
}

function calculateAgeDays(value) {
    const date = parseDashboardDate(value);
    if (Number.isNaN(date.getTime())) return "Não informado";

    const diffMs = Date.now() - date.getTime();
    return Math.max(0, Math.floor(diffMs / 86400000));
}

function getOperationalStatusRank(status) {
    const normalizedStatus = String(status || "").toLowerCase();

    if (normalizedStatus.includes("novo")) return 0;
    if (normalizedStatus.includes("aberto")) return 1;
    if (normalizedStatus.includes("pendente")) return 2;
    if (normalizedStatus.includes("fechado")) return 4;
    return 3;
}

function getOperationalPriorityRank(priority) {
    const match = String(priority || "").match(/\d+/);
    return match ? Number(match[0]) : 0;
}

function getTimestamp(value) {
    const date = parseDashboardDate(value);
    return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function getAgeDaysForSort(value) {
    const age = calculateAgeDays(value);
    return Number.isFinite(age) ? age : -1;
}

function buildRiskChart(records) {
    const ranges = [
        { label: "1 a 7 dias", min: 1, max: 7 },
        { label: "8 a 15 dias", min: 8, max: 15 },
        { label: "+15 dias (Crítico)", min: 16, max: Infinity },
    ];
    const ages = records
        .map((item) => calculateAgeDays(item.datacriacao))
        .filter((age) => Number.isFinite(age));

    return {
        labels: ranges.map((range) => range.label),
        values: ranges.map((range) => ages.filter((age) => age >= range.min && age <= range.max).length),
        worstCase: ages.length ? Math.max(...ages) : 0,
    };
}

function sortOperationalRecords(records) {
    return [...records].sort((a, b) => {
        const statusDiff = getOperationalStatusRank(a.estado) - getOperationalStatusRank(b.estado);
        if (statusDiff !== 0) return statusDiff;

        const priorityDiff = getOperationalPriorityRank(b.prioridade) - getOperationalPriorityRank(a.prioridade);
        if (priorityDiff !== 0) return priorityDiff;

        const ageDiff = getAgeDaysForSort(b.datacriacao) - getAgeDaysForSort(a.datacriacao);
        if (ageDiff !== 0) return ageDiff;

        const modifiedDiff = getTimestamp(b.datamodificacao) - getTimestamp(a.datamodificacao);
        if (modifiedDiff !== 0) return modifiedDiff;

        return getTimestamp(b.datacriacao) - getTimestamp(a.datacriacao);
    });
}

function buildKpis(records) {
    if (!allRecords.length) return data.kpis;

    const total = records.length;
    const n1 = records.filter((item) => item.fila === "SESUITE-N1").length;
    const n2 = records.filter((item) => item.fila === "SESUITE-N2").length;
    const n3 = records.filter((item) => item.fila === "SESUITE-N3").length;

    return [
        { label: "Total", value: total, color: "blue", icon: "list-checks" },
        { label: "N1", value: n1, color: "green", icon: "check-circle" },
        { label: "N2", value: n2, color: "amber", icon: "clock" },
        { label: "N3", value: n3, color: "red", icon: "alert-triangle" },
    ];
}

function buildProgress(records, kpis) {
    if (!allRecords.length) return data.progress.items;

    const total = kpis[0]?.value || 0;
    return [
        { label: "SESUITE-N1", value: kpis[1]?.value || 0, percent: percentualJS(kpis[1]?.value || 0, total), color: "green" },
        { label: "SESUITE-N2", value: kpis[2]?.value || 0, percent: percentualJS(kpis[2]?.value || 0, total), color: "amber" },
        { label: "SESUITE-N3", value: kpis[3]?.value || 0, percent: percentualJS(kpis[3]?.value || 0, total), color: "red" },
    ];
}

function renderKpis(records) {
    const kpis = buildKpis(records);

    document.getElementById("kpi-container").innerHTML = kpis
        .map((item) => `
        <article class="kpi-card tone-${item.color}">
            <div>
                <h3>${escapeHTML(item.label)}</h3>
                <p>${escapeHTML(item.value)}</p>
            </div>
            <div class="kpi-icon"><i data-lucide="${item.icon}"></i></div>
        </article>
    `)
        .join("");

    return kpis;
}

function renderProgress(records, kpis) {
    const progressItems = buildProgress(records, kpis);
    const total = kpis[0]?.value || 0;

    document.getElementById("progress-container").innerHTML = progressItems
        .map((item) => `
        <div class="progress-item">
            <div class="progress-meta">
                <strong>${escapeHTML(item.label)}</strong>
                <span>${escapeHTML(item.percent)}% (${escapeHTML(item.value)}/${escapeHTML(total)})</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill tone-${item.color}" style="width: ${item.percent}%"></div>
            </div>
        </div>
    `)
        .join("");
}

function applyFilters() {
    const nivel = document.getElementById("filter-nivel")?.value || "";
    const tipo = document.getElementById("filter-tipo")?.value || "";
    const executor = document.getElementById("filter-executor")?.value || "";
    const status = document.getElementById("filter-status")?.value || "";
    const titulo = (document.getElementById("filter-titulo")?.value || "").toLowerCase();

    filteredRecords = allRecords.filter((item) => {
        const matchNivel = !nivel || item.fila === nivel;
        const matchTipo = !tipo || item.tipo === tipo;
        const matchExecutor = !executor || item.proprietarionome === executor;
        const matchStatus = !status || item.estado === status;
        const matchTitulo = !titulo || String(item.titulo || "").toLowerCase().includes(titulo);

        return matchNivel && matchTipo && matchExecutor && matchStatus && matchTitulo;
    });

    renderDashboard(filteredRecords);
}

fillSelect("filter-nivel", data.filters?.niveis || [], "Todos os níveis");
fillSelect("filter-tipo", data.filters?.tipos || [], "Todos os tipos");
fillSelect("filter-executor", data.filters?.executores || [], "Todos");
fillSelect("filter-status", data.filters?.status || [], "Todos os status");

["filter-nivel", "filter-tipo", "filter-executor", "filter-status", "filter-titulo"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", applyFilters);
});

document.getElementById("clear-filters")?.addEventListener("click", () => {
    ["filter-nivel", "filter-tipo", "filter-executor", "filter-status", "filter-titulo"].forEach((id) => {
        const element = document.getElementById(id);
        if (element) element.value = "";
    });
    applyFilters();
});

filterToggle?.addEventListener("click", () => {
    const isHidden = filterBody?.hidden;
    if (!filterBody) return;

    filterBody.hidden = !isHidden;
    filterToggle.title = filterBody.hidden ? "Expandir filtros" : "Recolher filtros";
    filterToggle.innerHTML = filterBody.hidden
        ? '<i data-lucide="chevron-down" data-fallback="⌄"></i>'
        : '<i data-lucide="chevron-up" data-fallback="⌃"></i>';
    refreshIcons();
});

// Paleta de Cores e Configurações base dos gráficos
const palette = ["#1677ff", "#198f55", "#ffb800", "#e6374d", "#19c2dd", "#6f7a82", "#111827"];

function getThemeColors() {
    const isDark = document.documentElement.dataset.theme === "dark";

    return {
        text: isDark ? "#d9dee8" : "#626a73",
        grid: isDark ? "#2d3446" : "#e4e8ee",
        label: isDark ? "#f3f5f9" : "#1a1f36",
    };
}

function chartBaseOptions() {
    const colors = getThemeColors();

    return {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { left: 15, right: 25, top: 15, bottom: 5 } },
        plugins: {
            legend: {
                position: "bottom",
                labels: { color: colors.text, boxWidth: 12, font: { size: 11 } }
            },
            datalabels: {
                color: colors.label,
                font: { weight: "bold", size: 10 },
                anchor: "end",
                align: "top",
                formatter: (value) => value > 0 ? value : ""
            }
        },
        scales: {
            x: { ticks: { color: colors.text, font: { family: "Inter" } }, grid: { color: colors.grid } },
            y: { ticks: { color: colors.text, font: { family: "Inter" } }, grid: { color: colors.grid } }
        }
    };
}

function horizontalOptions(options = {}) {
    const colors = getThemeColors();
    const base = chartBaseOptions();
    const labelWidth = options.labelWidth || 140;
    const barPercentage = options.barPercentage || 0.6;
    const categoryPercentage = options.categoryPercentage || 1.0;
    const labelPadding = options.labelPadding ?? 6;
    const labelCrossAlign = options.labelCrossAlign || "center";
    const forceLabelWidth = options.forceLabelWidth || false;

    return {
        ...base,
        indexAxis: "y",
        layout: { padding: { right: 40 } },

        barPercentage: barPercentage,
        categoryPercentage: categoryPercentage,

        scales: {
            x: {
                ticks: { color: colors.text, font: { family: "Inter" } },
                grid: { color: colors.grid }
            },
            y: {
                afterFit: function(scaleInstance) {
                    if (forceLabelWidth) {
                        scaleInstance.width = labelWidth;
                        return;
                    }

                    if (scaleInstance.width < labelWidth) {
                        scaleInstance.width = labelWidth;
                    }
                },
                ticks: {
                    color: colors.text,
                    font: {
                        family: "Inter",
                        size: 11,
                        lineHeight: 1.4
                    },
                    padding: labelPadding,
                    crossAlign: labelCrossAlign,
                    autoSkip: false,
                    callback: function(value) {
                        const label = this.getLabelForValue(value) || '';

                        if (label.length <= 25) return label;

                        const words = label.split(' ');
                        const lines = [];
                        let currentLine = '';

                        words.forEach(word => {
                            if ((currentLine + word).length > 25) {
                                lines.push(currentLine.trim());
                                currentLine = word + ' ';
                            } else {
                                currentLine += word + ' ';
                            }
                        });
                        if (currentLine.trim() !== '') {
                            lines.push(currentLine.trim());
                        }

                        return lines;
                    }
                },
                grid: { display: false }
            }
        },
        plugins: {
            ...base.plugins,
            tooltip: {
                callbacks: {
                    title: function(context) {
                        return context[0].chart.data.labels[context[0].dataIndex];
                    }
                }
            },
            datalabels: {
                color: colors.label, font: { weight: "bold", size: 11 },
                anchor: "end", align: "right", display: true, formatter: (value) => value
            }
        }
    };
}

// ... (seu código horizontalOptions acima) ...

function verticalOptions() {
    const colors = getThemeColors();
    const base = chartBaseOptions();

    return {
        ...base,
        barPercentage: 0.6,
        categoryPercentage: 0.8,
        layout: { padding: { top: 30, bottom: 10 } }, // Dá espaço para o número no topo da barra
        scales: {
            x: {
                ticks: {
                    color: colors.text,
                    font: { family: "Inter", size: 11 },
                    autoSkip: false,
                    maxRotation: 45, // Força a inclinação do texto
                    minRotation: 45  // Mantém a inclinação fixa
                },
                grid: { display: false } // Remove as linhas verticais
            },
            y: {
                ticks: { color: colors.text, font: { family: "Inter" } },
                grid: { color: colors.grid }
            }
        },
        plugins: {
            ...base.plugins,
            tooltip: {
                callbacks: {
                    title: function(context) {
                        return context[0].chart.data.labels[context[0].dataIndex];
                    }
                }
            },
            datalabels: {
                color: colors.label, font: { weight: "bold", size: 11 },
                anchor: "end", align: "top", display: true, formatter: (value) => value
            }
        }
    };
}

function riskOptions() {
    const colors = getThemeColors();
    const base = chartBaseOptions();

    return {
        ...base,
        maintainAspectRatio: false,
        layout: { padding: { left: 8, right: 10, top: 22, bottom: 0 } },
        barPercentage: 0.55,
        categoryPercentage: 0.85,
        scales: {
            x: {
                ticks: {
                    color: colors.text,
                    font: { family: "Inter", size: 11 },
                    maxRotation: 0,
                    minRotation: 0,
                    autoSkip: false,
                },
                grid: { display: false },
            },
            y: {
                beginAtZero: true,
                ticks: { color: colors.text, font: { family: "Inter", size: 11 }, precision: 0 },
                grid: { color: colors.grid },
            },
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (context) => `${context.parsed.y} chamados`,
                },
            },
            datalabels: {
                color: colors.label,
                font: { weight: "bold", size: 11 },
                anchor: "end",
                align: "top",
                formatter: (value) => value,
            },
        },
    };
}

// --- NOVA CONFIGURAÇÃO PARA AS ROSCAS NÃO CORTAREM ---
function doughnutOptions() {
    const base = chartBaseOptions();

    return {
        ...base,
        layout: { padding: 20 }, // Margem igual em todos os lados para não esmagar a rosca
        scales: { x: { display: false }, y: { display: false } }, // Roscas não têm eixo X/Y
        plugins: {
            ...base.plugins,
            datalabels: { color: "#fff", formatter: (value) => value > 0 ? value : "" }
        }
    };
}


// Renderização dos Gráficos
let chartInstances = [];

function buildTimeline(records) {
    if (!allRecords.length) return data.charts.timeline;

    const monthFormatter = new Intl.DateTimeFormat("pt-BR", { month: "short", year: "numeric" });
    const monthKeys = [...new Set(records
        .map((item) => String(item.datacriacao || "").slice(0, 7))
        .filter((value) => /^\d{4}-\d{2}$/.test(value))
    )].sort();

    const countMonth = (fila = null) => monthKeys.map((month) => records.filter((item) => {
        const matchMonth = String(item.datacriacao || "").startsWith(month);
        const matchFila = !fila || item.fila === fila;
        return matchMonth && matchFila;
    }).length);

    return {
        labels: monthKeys.map((month) => {
            const [year, monthNumber] = month.split("-").map(Number);
            return monthFormatter.format(new Date(year, monthNumber - 1, 1));
        }),
        total: countMonth(),
        n1: countMonth("SESUITE-N1"),
        n2: countMonth("SESUITE-N2"),
        n3: countMonth("SESUITE-N3"),
    };
}

function buildCharts(records) {
    if (!allRecords.length) return data.charts;

    return {
        tipos: chartFromCounts(records, "tipo"),
        filas: chartFromCounts(records, "fila"),
        estados: chartFromCounts(records, "estado"),
        analistas: chartFromCounts(records, "proprietarionome", 10),
        servicos: chartFromCounts(records, "servico", 10),
        riscos: buildRiskChart(records),
        timeline: buildTimeline(records),
    };
}

function getNiceAxisMax(values) {
    const maxValue = Math.max(0, ...values);
    if (maxValue <= 0) return 100;

    const step = maxValue <= 100 ? 50 : 100;
    return Math.ceil(maxValue / step) * step;
}

function renderAnalystsChart(analistas) {
    const chart = document.getElementById("chartAnalistas");
    if (!chart) return;

    if (!analistas.labels.length) {
        chart.innerHTML = `<div class="table-empty">Nenhum analista encontrado para os filtros selecionados.</div>`;
        return;
    }

    const axisMax = getNiceAxisMax(analistas.values);
    const ticks = [0, axisMax / 3, axisMax * 2 / 3, axisMax].map((value) => Math.round(value));
    const rows = analistas.labels.map((label, index) => {
        const value = analistas.values[index] || 0;
        const width = Math.min(100, percentualJS(value, axisMax));

        return `
            <div class="analysts-row">
                <div class="analysts-name">${escapeHTML(label)}</div>
                <div class="analysts-plot">
                    <div class="analysts-bar" style="width: ${width}%">
                        <span class="analysts-value">${escapeHTML(value)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join("");

    chart.innerHTML = `
        <div class="analysts-chart-body">${rows}</div>
        <div class="analysts-axis">
            <span></span>
            <div class="analysts-axis-ticks">
                ${ticks.map((tick) => `<span>${escapeHTML(tick)}</span>`).join("")}
            </div>
        </div>
        <div class="analysts-legend">Atendimentos</div>
    `;
}

function renderCharts(records = filteredRecords) {
    if (!window.Chart || !hasInjectedData) {
        return;
    }

    const charts = buildCharts(records);

    chartInstances.forEach((chart) => chart.destroy());
    chartInstances = [];

    chartInstances.push(new Chart(document.getElementById("chartTimeline"), {
        type: "line",
        data: {
            labels: charts.timeline.labels,
            datasets: [
                { label: "Total", data: charts.timeline.total, borderColor: "#1677ff", backgroundColor: "#1677ff", tension: 0.2 },
                { label: "N1", data: charts.timeline.n1, borderColor: "#198f55", backgroundColor: "#198f55", tension: 0.2 },
                { label: "N2", data: charts.timeline.n2, borderColor: "#ffb800", backgroundColor: "#ffb800", tension: 0.2 },
                { label: "N3", data: charts.timeline.n3, borderColor: "#e6374d", backgroundColor: "#e6374d", tension: 0.2 }
            ]
        },
        options: chartBaseOptions()
    }));

    chartInstances.push(new Chart(document.getElementById("chartTipos"), {
        type: "doughnut",
        data: { labels: charts.tipos.labels, datasets: [{ data: charts.tipos.values, backgroundColor: palette }] },
        options: doughnutOptions()
    }));

    chartInstances.push(new Chart(document.getElementById("chartFilas"), {
        type: "doughnut",
        data: { labels: charts.filas.labels, datasets: [{ data: charts.filas.values, backgroundColor: ["#4ade80", "#ffbd45", "#ff5f52"] }] },
        options: doughnutOptions()
    }));

    chartInstances.push(new Chart(document.getElementById("chartEstados"), {
        type: "bar",
        data: { labels: charts.estados.labels, datasets: [{ label: "Qtd", data: charts.estados.values, backgroundColor: ["#4ade80", "#1677ff", "#ffbd45"], borderRadius: 8 }] },
        options: horizontalOptions()
    }));

    const riskWorstCase = document.getElementById("risk-worst-case");
    if (riskWorstCase) {
        riskWorstCase.innerText = `Pior caso: ${charts.riscos.worstCase} dias de atraso`;
    }

    chartInstances.push(new Chart(document.getElementById("chartRiscos"), {
        type: "bar",
        data: {
            labels: charts.riscos.labels,
            datasets: [{
                label: "Qtd",
                data: charts.riscos.values,
                backgroundColor: ["#ffb800", "#ffb800", "#e6374d"],
                borderRadius: 4,
            }],
        },
        options: riskOptions(),
    }));

    renderAnalystsChart(charts.analistas);
}

function renderServicesTable(records) {
    const servicos = allRecords.length ? chartFromCounts(records, "servico", 10) : data.charts.servicos;
    const table = document.getElementById("tableServicos");
    if (!table) return;

    if (!servicos.labels.length) {
        table.innerHTML = `<div class="table-empty">Nenhum serviço encontrado para os filtros selecionados.</div>`;
        return;
    }

    let tableHTML = `
        <table class="ranking-table">
            <thead>
                <tr>
                    <th style="width: 50px; text-align: center;">Pos</th>
                    <th>Nome do Serviço</th>
                    <th style="text-align: right; width: 60px;">Qtd</th>
                </tr>
            </thead>
            <tbody>
    `;

    servicos.labels.forEach((label, index) => {
        const rank = index + 1;
        const badgeClass = rank <= 3 ? "rank-badge rank-top3" : "rank-badge";

        tableHTML += `
            <tr>
                <td style="text-align: center;"><span class="${badgeClass}">${rank}º</span></td>
                <td style="word-wrap: anywhere; font-weight: 500;">${escapeHTML(label)}</td>
                <td style="text-align: right; font-weight: 800;">${escapeHTML(servicos.values[index])}</td>
            </tr>
        `;
    });

    tableHTML += `</tbody></table>`;
    table.innerHTML = tableHTML;
}

function renderOperationalTable(records) {
    const table = document.getElementById("operational-table");
    if (!table) return;

    if (!records.length) {
        table.innerHTML = `<div class="table-empty">Nenhum chamado encontrado para os filtros selecionados.</div>`;
        return;
    }

    const prioritizedRecords = sortOperationalRecords(records);
    const rows = prioritizedRecords.map((item) => `
        <tr>
            <td>${escapeHTML(item.numerochamado || "Não informado")}</td>
            <td class="title-cell">${escapeHTML(item.titulo || "Não informado")}</td>
            <td>${escapeHTML(item.fila || "Não informado")}</td>
            <td>${escapeHTML(item.estado || "Não informado")}</td>
            <td>${escapeHTML(item.proprietarionome || "Não informado")}</td>
            <td>${escapeHTML(item.servico || "Não informado")}</td>
            <td>${escapeHTML(item.prioridade || "Não informado")}</td>
            <td>${escapeHTML(formatDateBR(item.datacriacao))}</td>
            <td>${escapeHTML(formatDateBR(item.datamodificacao))}</td>
            <td class="numeric-cell">${escapeHTML(calculateAgeDays(item.datacriacao))}</td>
        </tr>
    `).join("");

    table.innerHTML = `
        <table class="ranking-table operational-table">
            <thead>
                <tr>
                    <th>Chamado</th>
                    <th>Título</th>
                    <th>Nível</th>
                    <th>Status</th>
                    <th>Executor</th>
                    <th>Serviço</th>
                    <th>Prioridade</th>
                    <th>Criação</th>
                    <th>Modificação</th>
                    <th>Dias</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function renderDashboard(records) {
    updateResultCount(records);
    updateEmptyState(records);
    const kpis = renderKpis(records);
    renderProgress(records, kpis);
    renderCharts(records);
    renderServicesTable(records);
    renderOperationalTable(records);
    refreshIcons();
}

renderDashboard(filteredRecords);
