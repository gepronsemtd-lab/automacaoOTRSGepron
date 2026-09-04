Chart.register(ChartDataLabels);

// Lê os dados que o Python injetou no HTML
const data = window.DASHBOARD_DATA;
const allRecords = data.records || [];
let filteredRecords = [...allRecords];

const syncButton = document.getElementById("sync-button");
const logoutButton = document.getElementById("logout-button");
const themeToggle = document.getElementById("theme-toggle");
const filterBody = document.getElementById("filter-body");
const filterToggle = document.getElementById("filter-toggle");

function updateThemeButton() {
    if (!themeToggle) return;

    const isDark = document.documentElement.dataset.theme === "dark";
    themeToggle.title = isDark ? "Alternar para tema claro" : "Alternar para tema escuro";
    themeToggle.innerHTML = isDark
        ? '<i data-lucide="sun"></i>'
        : '<i data-lucide="moon"></i>';
    lucide.createIcons();
}

themeToggle?.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem("dashboardTheme", nextTheme);
    updateThemeButton();
    renderCharts();
});

const savedTheme = localStorage.getItem("dashboardTheme");
if (savedTheme) {
    document.documentElement.dataset.theme = savedTheme;
}
updateThemeButton();

syncButton?.addEventListener("click", async () => {
    syncButton.disabled = true;
    syncButton.querySelector("span").innerText = "Sincronizando...";

    try {
        const response = await fetch("/sync", { method: "POST" });
        if (!response.ok) throw new Error("Falha na sincronização");
        window.location.reload();
    } catch (error) {
        alert("Não foi possível sincronizar agora.");
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
document.getElementById("period-info").innerText = data.period;

// Funcionalidade de clique nas abas
const tabButtons = document.querySelectorAll('.tab-button');
tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Remove a cor azul de todas as abas
        tabButtons.forEach(btn => btn.classList.remove('active'));
        
        // Adiciona a cor azul apenas na aba que foi clicada
        button.classList.add('active');
        
        // Lógica a ser adicionada....
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
    const gerencia = document.getElementById("filter-gerencia")?.value || "";
    const executor = document.getElementById("filter-executor")?.value || "";
    const status = document.getElementById("filter-status")?.value || "";
    const titulo = (document.getElementById("filter-titulo")?.value || "").toLowerCase();

    filteredRecords = allRecords.filter((item) => {
        const matchNivel = !nivel || item.fila === nivel;
        const matchGerencia = !gerencia || item.gerencia === gerencia;
        const matchExecutor = !executor || item.proprietarionome === executor;
        const matchStatus = !status || item.estado === status;
        const matchTitulo = !titulo || String(item.titulo || "").toLowerCase().includes(titulo);

        return matchNivel && matchGerencia && matchExecutor && matchStatus && matchTitulo;
    });

    renderDashboard(filteredRecords);
}

fillSelect("filter-nivel", data.filters?.niveis || [], "Todos os níveis");
fillSelect("filter-gerencia", data.filters?.gerencias || [], "Todas");
fillSelect("filter-executor", data.filters?.executores || [], "Todos");
fillSelect("filter-status", data.filters?.status || [], "Todos os status");

["filter-nivel", "filter-gerencia", "filter-executor", "filter-status", "filter-titulo"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", applyFilters);
});

document.getElementById("clear-filters")?.addEventListener("click", () => {
    ["filter-nivel", "filter-gerencia", "filter-executor", "filter-status", "filter-titulo"].forEach((id) => {
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
        ? '<i data-lucide="chevron-down"></i>'
        : '<i data-lucide="chevron-up"></i>';
    lucide.createIcons();
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

function horizontalOptions() {
    const colors = getThemeColors();
    const base = chartBaseOptions();

    return {
        ...base,
        indexAxis: "y",
        layout: { padding: { right: 40 } },

        barPercentage: 0.6,       // Deixa as barras mais finas (o padrão é 0.9)
        categoryPercentage: 1.0,  // Aumenta a distância entre uma barra e outra

        scales: {
            x: {
                ticks: { color: colors.text, font: { family: "Inter" } },
                grid: { color: colors.grid }
            },
            y: {
                afterFit: function(scaleInstance) {
                    if (scaleInstance.width < 140) {
                        scaleInstance.width = 140;
                    }
                },
                ticks: {
                    color: colors.text,
                    font: {
                        family: "Inter",
                        size: 11,
                        lineHeight: 1.4
                    },
                    padding: 6, // <-- AFASTA O TEXTO DAS BARRAS HORIZONTALMENTE
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
        timeline: buildTimeline(records),
    };
}

function renderCharts(records = filteredRecords) {
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

    chartInstances.push(new Chart(document.getElementById("chartAnalistas"), {
        type: "bar",
        data: { labels: charts.analistas.labels, datasets: [{ label: "Atendimentos", data: charts.analistas.values, backgroundColor: "#8b5cf6", borderRadius: 8 }] },
        options: horizontalOptions()
    }));
}

function renderServicesTable(records) {
    const servicos = allRecords.length ? chartFromCounts(records, "servico", 10) : data.charts.servicos;

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
    document.getElementById("tableServicos").innerHTML = tableHTML;
}

function renderDashboard(records) {
    const kpis = renderKpis(records);
    renderProgress(records, kpis);
    renderCharts(records);
    renderServicesTable(records);
    lucide.createIcons();
}

renderDashboard(filteredRecords);
