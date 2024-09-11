Chart.defaults.font.family = 'Onest';
var i = 0

document.querySelectorAll('[data-id="report-tab"]').forEach(function(tab) {

    var products_title = products_titles[i];
    var products_sum = products_sums[i];
    var products_quantity = products_quantities[i];
    var orders_data = orders_datas[i];
    i++;

    if (products_title) {

        const getOrCreateLegendList = (chart, DataID) => {
            console.log(DataID)
            const legendContainer = tab.querySelector(DataID);
            let listContainer = legendContainer.querySelector('ul');
          
            if (!listContainer) {
              listContainer = document.createElement('ul');          
              legendContainer.appendChild(listContainer);
            }
          
            return listContainer;
        };
        const htmlLegendPlugin = {
            id: 'htmlLegend',
            afterUpdate(chart, args, options) {
                console.log(options);
            const ul = getOrCreateLegendList(chart, options.containerDataID);
        
            // Remove old legend items
            while (ul.firstChild) {
                ul.firstChild.remove();
            }
        
            // Reuse the built-in legendItems generator
            const items = chart.options.plugins.legend.labels.generateLabels(chart);
        
            items.forEach(item => {
                const li = document.createElement('li');
        
                li.onclick = () => {
                const {type} = chart.config;
                if (type === 'pie' || type === 'doughnut') {
                    // Pie and doughnut charts only have a single dataset and visibility is per item
                    chart.toggleDataVisibility(item.index);
                } else {
                    chart.setDatasetVisibility(item.datasetIndex, !chart.isDatasetVisible(item.datasetIndex));
                }
                chart.update();
                };
        
                // Color box
                const boxSpan = document.createElement('span');
                boxSpan.style.background = item.fillStyle;
                boxSpan.style.borderColor = item.strokeStyle
        
                // Text
                const textContainer = document.createElement('p');
                textContainer.style.textDecoration = item.hidden ? 'line-through' : '';
        
                const text = document.createTextNode(item.text);
                textContainer.appendChild(text);
        
                li.appendChild(boxSpan);
                li.appendChild(textContainer);
                ul.appendChild(li);
            });
            }
        };


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
                    htmlLegend: {
                        containerDataID: '[data-id="legend-price-chart"]',
                    },
                    legend: {
                        display: false,
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
            },
            plugins: [htmlLegendPlugin],
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
                    htmlLegend: {
                        containerDataID: '[data-id="legend-count-chart"]',
                    },
                    legend: {
                        display: false,
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
            },
            plugins: [htmlLegendPlugin],
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
                    htmlLegend: {
                        containerDataID: '[data-id="legend-graph-chart"]',
                    },
                    legend: {
                        display: false,
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
            
            },
            plugins: [htmlLegendPlugin],
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
    
        var prev_btn = tab.querySelector('[data-id="prev-page"]');
        prev_btn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                updateChart(currentPage);
            }
        });
    
        var next_btn = tab.querySelector('[data-id="next-page"]');
        next_btn.addEventListener('click', () => {
            if (currentPage * itemsPerPage < orders_data.labels.length) {
                currentPage++;
                updateChart(currentPage);
            }
        });

        var range_container = tab.querySelector('[data-id="range-container"]');
        var range_value = range_container.querySelector('[data-id="range-value"]');
        var range_input = range_container.querySelector('[data-id="graph-range"]');
        range_input.value = itemsPerPage;
        range_value.textContent = itemsPerPage;
        range_input.addEventListener('input', function() {
            itemsPerPage = range_input.value;
            range_value.textContent = itemsPerPage;
            currentPage = Math.ceil(orders_data.labels.length / itemsPerPage);
            updateChart(currentPage);
        });
    
        if (orders_data.labels.length <= itemsPerPage){
            prev_btn.classList.add('d-none');
            next_btn.classList.add('d-none');
            range_container.classList.add('d-none');
        } else if (range_input.max > orders_data.labels.length){
            range_input.max = orders_data.labels.length;
            range_container.querySelector('[data-id="range-max"]').textContent = orders_data.labels.length;
        }
        
        // Инициализируем график с первой страницей данных
        updateChart(currentPage);
    }
});