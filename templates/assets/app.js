Chart.register(ChartDataLabels);

// Lê os dados que o Python injetou no HTML
const data = window.DASHBOARD_DATA;

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
    layout: { padding: { left: 15, right: 25, top: 15, bottom: 5 } },
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
    
    barPercentage: 0.6,       // Deixa as barras mais finas (o padrão é 0.9)
    categoryPercentage: 1.0,  // Aumenta a distância entre uma barra e outra
    
    scales: {
        x: {
            ticks: { color: "#626a73", font: { family: "Inter" } },
            grid: { color: "#e4e8ee" }
        },
        y: {
            afterFit: function(scaleInstance) {
                if (scaleInstance.width < 140) {
                    scaleInstance.width = 140; 
                }
            },
            ticks: {
                color: "#626a73",
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
        ...commonOptions.plugins,
        tooltip: {
            callbacks: {
                title: function(context) {
                    return context[0].chart.data.labels[context[0].dataIndex];
                }
            }
        },
        datalabels: {
            color: "#1a1f36", font: { weight: "bold", size: 11 },
            anchor: "end", align: "right", display: true, formatter: (value) => value
        }
    }
};

// ... (seu código horizontalOptions acima) ...

const verticalOptions = {
    ...commonOptions,
    barPercentage: 0.6,       
    categoryPercentage: 0.8,  
    layout: { padding: { top: 30, bottom: 10 } }, // Dá espaço para o número no topo da barra
    scales: {
        x: {
            ticks: {
                color: "#626a73",
                font: { family: "Inter", size: 11 },
                autoSkip: false,
                maxRotation: 45, // Força a inclinação do texto
                minRotation: 45  // Mantém a inclinação fixa
            },
            grid: { display: false } // Remove as linhas verticais
        },
        y: {
            ticks: { color: "#626a73", font: { family: "Inter" } },
            grid: { color: "#e4e8ee" }
        }
    },
    plugins: {
        ...commonOptions.plugins,
        tooltip: {
            callbacks: {
                title: function(context) {
                    return context[0].chart.data.labels[context[0].dataIndex];
                }
            }
        },
        datalabels: {
            color: "#1a1f36", font: { weight: "bold", size: 11 },
            anchor: "end", align: "top", display: true, formatter: (value) => value
        }
    }
};

// --- NOVA CONFIGURAÇÃO PARA AS ROSCAS NÃO CORTAREM ---
const doughnutOptions = {
    ...commonOptions,
    layout: { padding: 20 }, // Margem igual em todos os lados para não esmagar a rosca
    scales: { x: { display: false }, y: { display: false } }, // Roscas não têm eixo X/Y
    plugins: {
        ...commonOptions.plugins,
        datalabels: { color: "#fff", formatter: (value) => value > 0 ? value : "" }
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
    options: doughnutOptions
});

new Chart(document.getElementById("chartFilas"), {
    type: "doughnut",
    data: { labels: data.charts.filas.labels, datasets: [{ data: data.charts.filas.values, backgroundColor: ["#4ade80", "#ffbd45", "#ff5f52"] }] },
    options: doughnutOptions 
});

new Chart(document.getElementById("chartEstados"), {
    type: "bar",
    data: { labels: data.charts.estados.labels, datasets: [{ label: "Qtd", data: data.charts.estados.values, backgroundColor: ["#4ade80", "#1677ff", "#ffbd45"], borderRadius: 8 }] },
    options: horizontalOptions
});

new Chart(document.getElementById("chartAnalistas"), {
    type: "bar",
    data: { labels: data.charts.analistas.labels, datasets: [{ label: "Atendimentos", data: data.charts.analistas.values, backgroundColor: "#8b5cf6", borderRadius: 8 }] },
    options: horizontalOptions
});

// Renderização da Tabela de Top 10 Serviços
const servicosLabels = data.charts.servicos.labels;
const servicosValues = data.charts.servicos.values;

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

servicosLabels.forEach((label, index) => {
    const rank = index + 1;
    // Se for 1º, 2º ou 3º, ganha a cor dourada
    const badgeClass = rank <= 3 ? 'rank-badge rank-top3' : 'rank-badge'; 
    
    tableHTML += `
        <tr>
            <td style="text-align: center;"><span class="${badgeClass}">${rank}º</span></td>
            <!-- word-wrap garante que textos gigantes quebrem de linha sem estourar a tabela -->
            <td style="word-wrap: anywhere; font-weight: 500;">${label}</td>
            <td style="text-align: right; font-weight: 800;">${servicosValues[index]}</td>
        </tr>
    `;
});

tableHTML += `</tbody></table>`;
document.getElementById("tableServicos").innerHTML = tableHTML;

// Inicia os ícones no final
lucide.createIcons();

lucide.createIcons();