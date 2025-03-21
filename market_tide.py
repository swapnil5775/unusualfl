from flask import Blueprint, render_template_string, request
from common import get_api_data, MENU_BAR
import logging
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

market_tide_bp = Blueprint('market_tide', __name__, url_prefix='/')

@market_tide_bp.route('/market-tide')
def market_tide():
    period = request.args.get('period', 'day')
    
    # Generate mock data
    sectors = ['Technology', 'Healthcare', 'Financials', 'Consumer', 'Energy', 'Materials']
    data = []
    
    for sector in sectors:
        value = random.uniform(-5, 5)
        data.append({
            'sector': sector,
            'value': value,
            'color': 'rgba(40, 167, 69, 0.7)' if value > 0 else 'rgba(220, 53, 69, 0.7)'
        })
    
    html = """
    {{ style }}
    <div class="container">
        <h1>Market Tide</h1>
        """ + MENU_BAR + """
        
        <div class="card">
            <div class="period-selector">
                <a href="?period=day" class="btn {% if period == 'day' %}active{% endif %}">Day</a>
                <a href="?period=week" class="btn {% if period == 'week' %}active{% endif %}">Week</a>
                <a href="?period=month" class="btn {% if period == 'month' %}active{% endif %}">Month</a>
                <a href="?period=year" class="btn {% if period == 'year' %}active{% endif %}">Year</a>
            </div>
            
            <div class="chart-container">
                <canvas id="marketTideChart"></canvas>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Sector</th>
                            <th>Flow (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in data %}
                        <tr>
                            <td>{{ item.sector }}</td>
                            <td style="color: {{ 'green' if item.value > 0 else 'red' }}">
                                {{ "%.2f"|format(item.value) }}%
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <style>
        .period-selector {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }
        
        .btn.active {
            background-color: var(--secondary-color);
        }
        
        .chart-container {
            margin: 20px 0;
            height: 400px;
        }
        
        .table-container {
            margin-top: 20px;
        }
    </style>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const ctx = document.getElementById('marketTideChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: {{ [item.sector for item in data] | tojson }},
                datasets: [{
                    label: 'Market Flow (%)',
                    data: {{ [item.value for item in data] | tojson }},
                    backgroundColor: {{ [item.color for item in data] | tojson }},
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'var(--border)'
                        },
                        ticks: {
                            color: 'var(--text)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'var(--border)'
                        },
                        ticks: {
                            color: 'var(--text)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'var(--text)'
                        }
                    }
                }
            }
        });
    </script>
    """
    
    return render_template_string(html, period=period, data=data) 