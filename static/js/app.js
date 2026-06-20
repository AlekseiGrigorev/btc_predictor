let chartInstance = null; // Переменная для хранения экземпляра графика

// Вспомогательная функция для обновления статуса на экране
function setStatus(message, type = 'normal') {
    const el = document.getElementById('statusMessage');
    el.textContent = message;
    el.className = 'status ' + type;
}

// Вспомогательная функция для блокировки/разблокировки кнопок во время загрузки
function toggleButtons(disabled) {
    document.getElementById('btnLoad').disabled = disabled;
    document.getElementById('btnChart').disabled = disabled;
}

function getPatternsCount() {
    return parseInt(document.getElementById('patternsCount').value) || 5;
}

function getDaysCount() {
    return parseInt(document.getElementById('daysCount').value) || 30;
}

function getTimeframe() {
    return document.getElementById('timeframeSelect').value;
}

// 1. Загрузка данных
async function loadData() {
    const top_n = getPatternsCount();
    const days = getDaysCount();
    const timeframe = getTimeframe();

    toggleButtons(true);
    setStatus(`Загрузка данных (${timeframe})...`, 'loading');
    
    try {
        const response = await fetch('/api/load_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ top_n: top_n, days: days, timeframe: timeframe }),
        });
        
        const result = await response.json();
        if (response.ok) {
            setStatus(result.message || 'Данные успешно загружены!', 'success');
        } else {
            setStatus(`Ошибка: ${result.detail || 'Не удалось загрузить данные'}`, 'error');
        }
    } catch (error) {
        setStatus('Ошибка сети или сервера', 'error');
        console.error(error);
    } finally {
        toggleButtons(false);
    }
}

// 2. Поиск паттернов и построение графика
async function buildChart() {
    const top_n = getPatternsCount();
    const days = getDaysCount();
    const timeframe = getTimeframe();

    toggleButtons(true);
    setStatus(`Поиск паттернов (${timeframe})...`, 'loading');

    try {
        const response = await fetch(`/api/chart_data?top_n=${top_n}&days=${days}&timeframe=${timeframe}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Нет данных для построения');
        }

        renderPatternsChart(data.patterns, data.reference);
        setStatus('График построен', 'success');
    } catch (error) {
        setStatus(`Ошибка: ${error.message}`, 'error');
    } finally {
        toggleButtons(false);
    }
}

// Функция отрисовки графика паттернов с помощью Chart.js
function renderPatternsChart(patterns, reference) {
    const ctx = document.getElementById('stockChart').getContext('2d');

    // Если график уже существует, уничтожаем его перед созданием нового
    if (chartInstance) {
        chartInstance.destroy();
    }

    // Ось X: индексы от 0 до максимальной длины данных среди всех паттернов
    const maxLen = Math.max(...patterns.map(p => p.data.length));
    const labels = Array.from({length: maxLen}, (_, i) => i);

    // Формируем датасеты для каждого паттерна
    const datasets = [];

    // Добавляем эталонный паттерн (жирная красная сплошная линия) — первым, чтобы быть на переднем плане
    if (reference && reference.data && reference.data.length > 0) {
        datasets.push({
            label: `Эталон (${reference.label})`,
            data: reference.data,
            borderColor: '#dc3545',
            borderWidth: 4,
            tension: 0.1,
            spanGaps: false
        });
    }

    // Добавляем найденные паттерны (пунктирные цветные линии)
    patterns.forEach((pattern, index) => {
        // Равномерно распределяем цвета по цветовому кругу HSL
        const hue = (index * 360 / patterns.length) % 360;
        datasets.push({
            label: pattern.label,
            data: pattern.data,
            borderColor: `hsl(${hue}, 70%, 50%)`,
            borderWidth: 2,
            borderDash: [5, 5], // пунктирная линия
            tension: 0.1,
            spanGaps: false
        });
    });

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Найденные паттерны`
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: { display: true, text: 'Цена' }
                },
                x: {
                    title: { display: true, text: 'Индекс' }
                }
            }
        }
    });
}
