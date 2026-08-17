Chart.register(ChartDataLabels);

// Lê os dados que o Python injetou no HTML
const data = window.DASHBOARD_DATA;

// Preenche os textos de cabeçalho
document.getElementById("update-info").innerText = `Sincronizado: ${data.updated}`;
document.getElementById("period-info").innerText = data.period;

// Renderiza KPIs
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

// Renderiza Barras de Progresso
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

// Paleta de Cores e Configurações base dos gráficos
const palette = ["#1677ff", "#198f55", "#ffb800", "#e6374d", "#19c2dd", "#6f7a82", "#111827"];

const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } },
        datalabels: {
            color: "#444", font: { weight: "bold", size: 10 },
            anchor: "end", align: "top", formatter: (value) => value > 0 ? value : ""
        }
    },
    scales: {
        x: { ticks: { color: "#626a73", font: { family: "Inter" } }, grid: { color: "#e4e8ee" } },
        y: { ticks: { color: "#626a73", font: { family: "Inter" } }, grid: { color: "#e4e8ee" } }
    }
};

const horizontalOptions = {
    ...commonOptions,
    indexAxis: "y",
    layout: { padding: { right: 40 } },
    plugins: {
        ...commonOptions.plugins,
        datalabels: {
            color: "#1a1f36", font: { weight: "bold", size: 11 },
            anchor: "end", align: "right", display: true, formatter: (value) => value
        }
    }
};

// Renderização dos Gráficos
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
    data: { labels: data.charts.tipos.labels, datasets: [{ data: data.charts.tipos.values, backgroundColor: palette }] },
    options: { ...commonOptions, plugins: { ...commonOptions.plugins, datalabels: { color: "#fff", formatter: (value) => value > 0 ? value : "" } } }
});

new Chart(document.getElementById("chartFilas"), {
    type: "doughnut",
    data: { labels: data.charts.filas.labels, datasets: [{ data: data.charts.filas.values, backgroundColor: ["#4ade80", "#ffbd45", "#ff5f52"] }] },
    options: { ...commonOptions, plugins: { ...commonOptions.plugins, datalabels: { color: "#fff", formatter: (value) => value > 0 ? value : "" } } }
});

new Chart(document.getElementById("chartEstados"), {
    type: "bar",
    data: { labels: data.charts.estados.labels, datasets: [{ label: "Qtd", data: data.charts.estados.values, backgroundColor: palette, borderRadius: 8 }] },
    options: commonOptions
});

new Chart(document.getElementById("chartAnalistas"), {
    type: "bar",
    data: { labels: data.charts.analistas.labels, datasets: [{ label: "Atendimentos", data: data.charts.analistas.values, backgroundColor: "#8b5cf6", borderRadius: 8 }] },
    options: horizontalOptions
});

new Chart(document.getElementById("chartServicos"), {
    type: "bar",
    data: { labels: data.charts.servicos.labels, datasets: [{ label: "Qtd", data: data.charts.servicos.values, backgroundColor: "#1a1f36", borderRadius: 8 }] },
    options: horizontalOptions
});

lucide.createIcons();