Chart.defaults.font.family = 'Onest';
var i = 0

document.querySelectorAll('[data-id="report-tab"]').forEach(function(tab) {

    var products_title = products_titles[i];
    var products_sum = products_sums[i];
    var products_quantity = products_quantities[i];
    var orders_data = orders_datas[i];
    i++;

    if (products_title) {
        const PriceCtx = tab.querySelector('[data-id="price-chart"]').getContext('2d');
        const PriceChart = new Chart(PriceCtx, {
            type: 'doughnut',
            data: {
                labels: products_title,
                datasets: [{
                    label: 'Выручка по продуктам',
                    data: products_sum,
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
        const CountCtx = tab.querySelector('[data-id="count-chart"]').getContext('2d');
        const CountChart = new Chart(CountCtx, {
            type: 'doughnut',
            // type: 'polarArea',
            data: {
                labels: products_title,
                datasets: [{
                    label: 'Самые продаваемые продукты',
                    data: products_quantity,
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
    
        // Данные для диаграммы по количеству
        let itemsPerPage = 20;
        let currentPage = Math.ceil(orders_data.labels.length / itemsPerPage);
    
        var mobile = window.matchMedia('(min-width:768px)');
        if (!mobile.matches){
            itemsPerPage = 10;
        }
    
        const GraphCtx = tab.querySelector('[data-id="graph-chart"]').getContext('2d');
        const GraphChart = new Chart(GraphCtx, {
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
                                if (tooltipItem.dataset.label == "Сумма заказов"){
                                    return tooltipItem.dataset.label + ': ' + tooltipItem.raw.toFixed(0) + ' ₽';
                                }
                                return tooltipItem.dataset.label + ': ' + tooltipItem.raw.toFixed(0) + ' шт.';
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
    
            const pageLabels = orders_data.labels.slice(start, end);
            const pageData = orders_data.datasets.map(dataset => ({
                ...dataset,
                data: dataset.data.slice(start, end)
            }));
    
            GraphChart.data.labels = pageLabels;
            GraphChart.data.datasets = pageData;
            GraphChart.update();
            
            tab.querySelector('[data-id="page-info"]').textContent = pageLabels[0] + ' - ' + pageLabels[pageLabels.length - 1];
        }
    
        prev_btn = tab.querySelector('[data-id="prev-page"]');
        prev_btn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                updateChart(currentPage);
            }
        });
    
        next_btn = tab.querySelector('[data-id="next-page"]')
        next_btn.addEventListener('click', () => {
            if (currentPage * itemsPerPage < orders_data.labels.length) {
                currentPage++;
                updateChart(currentPage);
            }
        });
    
        if (orders_data.labels.length <= itemsPerPage){
            prev_btn.classList.add('d-none');
            next_btn.classList.add('d-none');
        }
    
        // Инициализируем график с первой страницей данных
        updateChart(currentPage);
    }
});