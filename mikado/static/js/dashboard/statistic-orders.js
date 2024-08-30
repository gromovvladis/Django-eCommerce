Chart.defaults.font.family = 'Onest';

const dayPriceCtx = document.getElementById('dayPriceChart').getContext('2d');
new Chart(dayPriceCtx, {
    type: 'doughnut',
    data: {
        labels: products_titles_days,
        datasets: [{
            label: 'Выручка по продуктам',
            data: products_sum_days,
            backgroundColor: [
                'rgba(255, 99, 132, 0.3)',
                'rgba(54, 162, 235, 0.3)',
                'rgba(255, 206, 86, 0.3)',
                'rgba(75, 192, 192, 0.3)',
                'rgba(153, 102, 255, 0.3)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 0.9)',
                'rgba(54, 162, 235, 0.9)',
                'rgba(255, 206, 86, 0.9)',
                'rgba(75, 192, 192, 0.9)',
                'rgba(153, 102, 255, 0.9)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
            },
            tooltip: {
                callbacks: {
                    label: function(tooltipItem) {
                        return tooltipItem.label + ': ' + tooltipItem.raw.toFixed(0) + " ₽";
                    }
                }
            },
            // datalabels: {
            //     display: true,
            // },
        },
    }
});

// Данные для диаграммы по количеству
const dayCountCtx = document.getElementById('dayCountChart').getContext('2d');
new Chart(dayCountCtx, {
    type: 'doughnut',
    // type: 'polarArea',
    data: {
        labels: products_titles_days,
        datasets: [{
            label: 'Самые продаваемые продукты',
            data: products_quantity_days,
            backgroundColor: [
                'rgba(255, 99, 132, 0.3)',
                'rgba(54, 162, 235, 0.3)',
                'rgba(255, 206, 86, 0.3)',
                'rgba(75, 192, 192, 0.3)',
                'rgba(153, 102, 255, 0.3)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 0.9)',
                'rgba(54, 162, 235, 0.9)',
                'rgba(255, 206, 86, 0.9)',
                'rgba(75, 192, 192, 0.9)',
                'rgba(153, 102, 255, 0.9)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
            },
            tooltip: {
                callbacks: {
                    label: function(tooltipItem) {
                        return tooltipItem.label + ': ' + tooltipItem.raw.toFixed(2) + " шт.";
                    }
                }
            },
            // datalabels: {
            //     display: true,
            // },
        }
    }
});



const itemsPerPage = 20;
let currentPage = Math.ceil(orders_data_days.labels.length / itemsPerPage);

// Данные для диаграммы по количеству
const dayGraphCtx = document.getElementById('dayGraphChart').getContext('2d');
const GraphChart = new Chart(dayGraphCtx, {
    type: 'bar',
    // data: orders_data_days,
    data: {
        labels: [],
        datasets: []
    },
    options: {
        plugins: {
            legend: {
                position: 'bottom',
            },
            // title: {
            //     display: true,
            //     text: 'Chart.js Bar Chart - Stacked'
            // },
            tooltip: {
                callbacks: {
                    label: function(tooltipItem) {
                        return tooltipItem.dataset.label + ': ' + tooltipItem.raw.toFixed(0) + ' ₽';
                    }
                }
            }
        },
        responsive: true,
        maintainAspectRatio: false, 
        scales: {
            x: {
                beginAtZero: true,
                stacked: false,
                ticks: {
                    autoSkip: false, // Отключаем автоматическое пропускание меток
                    maxRotation: 90, // Максимальный угол поворота меток оси X
                    minRotation: 45,
                    maxTicksLimit: 10,
                }
            },
            y: {
                beginAtZero: true,
                type: 'linear',
                display: true,
                position: 'left',
                // title: {
                //     display: true,
                //     text: 'Выручка',
                // }
            },
            y1: {
                beginAtZero: true,
                type: 'linear',
                display: true,
                position: 'right',
                grid: {
                    drawOnChartArea: false, // Скрывает сетку на этой оси
                },
                // title: {
                //     display: true,
                //     text: 'Заказы',
                // }
            }
        },
        interaction: {
            intersect: false,
        },
      
    }
    
});




function updateChart(page) {
    const start = (page - 1) * itemsPerPage;
    const end = page * itemsPerPage;

    const pageLabels = orders_data_days.labels.slice(start, end);
    const pageData = orders_data_days.datasets.map(dataset => ({
        ...dataset,
        data: dataset.data.slice(start, end)
    }));

    GraphChart.data.labels = pageLabels;
    GraphChart.data.datasets = pageData;
    GraphChart.update();
    
    document.getElementById('pageInfo').textContent = `Page ${page}`;
}

document.getElementById('prevPage').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        updateChart(currentPage);
    }
});

document.getElementById('nextPage').addEventListener('click', () => {
    if (currentPage * itemsPerPage < orders_data_days.labels.length) {
        currentPage++;
        updateChart(currentPage);
    }
});

// Инициализируем график с первой страницей данных
updateChart(currentPage);