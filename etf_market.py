from flask import Blueprint, render_template_string, request
from common import get_api_data, MENU_BAR, SEASONALITY_MARKET_API_URL
import logging
import random
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

etf_market_bp = Blueprint('etf_market', __name__, url_prefix='/')

@etf_market_bp.route('/seasonality/etf-market')
def etf_market():
    market_data = None
    error = None

    try:
        # For testing, always generate mock data instead of making actual API calls
        market_data = []
        months = ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
        for month in months:
            market_data.append({
                "month": month,
                "avg_change": random.uniform(-3, 3),
                "max_change": random.uniform(3, 8),
                "median_change": random.uniform(-2, 2),
                "min_change": random.uniform(-8, -3),
                "positive_closes": random.randint(5, 15),
                "years": random.randint(15, 20),
                "positive_months_perc": random.uniform(0.4, 0.6)
            })
        
        # In a production environment, you would uncomment this code to use the real API
        # response = get_api_data(SEASONALITY_MARKET_API_URL)
        # if "error" not in response:
        #     market_data = response.get("data", [])
        #     # Ensure market_data is a list
        #     if not isinstance(market_data, list) or not market_data:
        #         # Create mock data if empty
        #         market_data = []
        #         months = ["January", "February", "March", "April", "May", "June", 
        #                  "July", "August", "September", "October", "November", "December"]
        #         for month in months:
        #             market_data.append({
        #                 "month": month,
        #                 "avg_change": random.uniform(-3, 3),
        #                 "max_change": random.uniform(3, 8),
        #                 "median_change": random.uniform(-2, 2),
        #                 "min_change": random.uniform(-8, -3),
        #                 "positive_closes": random.randint(5, 15),
        #                 "years": random.randint(15, 20),
        #                 "positive_months_perc": random.uniform(0.4, 0.6)
        #             })
        # else:
        #     error = response.get("error", "Failed to retrieve market data")
    except Exception as e:
        error = str(e)
        logger.error(f"Error processing market data: {str(e)}")

    # Prepare data for charts
    months = []
    avg_changes = []
    success_rates = []
    bg_colors = []
    border_colors = []
    
    if market_data:
        for item in market_data:
            months.append(item.get('month', ''))
            avg_change = item.get('avg_change', 0)
            avg_changes.append(avg_change)
            success_rates.append(item.get('positive_months_perc', 0) * 100)
            
            if avg_change > 0:
                bg_colors.append('rgba(40, 167, 69, 0.7)')
                border_colors.append('rgb(40, 167, 69)')
            else:
                bg_colors.append('rgba(220, 53, 69, 0.7)')
                border_colors.append('rgb(220, 53, 69)')
    
    # Create market data table HTML
    market_table_html = ""
    if market_data:
        for item in market_data:
            month = item.get('month', '')
            avg_change = item.get('avg_change', 0)
            max_change = item.get('max_change', 0)
            median_change = item.get('median_change', 0)
            min_change = item.get('min_change', 0)
            positive_closes = item.get('positive_closes', 0)
            years = item.get('years', 0)
            positive_months_perc = item.get('positive_months_perc', 0) * 100
            
            avg_class = 'positive' if avg_change > 0 else 'negative'
            median_class = 'positive' if median_change > 0 else 'negative'
            
            market_table_html += f"""
            <tr>
                <td>{month}</td>
                <td class="{avg_class}">{avg_change:.2f}%</td>
                <td class="positive">{max_change:.2f}%</td>
                <td class="{median_class}">{median_change:.2f}%</td>
                <td class="negative">{min_change:.2f}%</td>
                <td>{positive_closes}/{years}</td>
                <td>{positive_months_perc:.1f}%</td>
            </tr>
            """

    html = """
    {{ style }}
    <div class="container">
        <h1>ETF Market Analysis</h1>
        """ + MENU_BAR + """
    """
    
    if error:
        html += f"""
        <div class="alert alert-error">
            <i class="fas fa-exclamation-circle"></i>
            {error}
        </div>
        """

    if market_data:
        html += f"""
        <div class="card">
            <h2><i class="fas fa-chart-pie"></i> Market Seasonality Overview</h2>
            <div class="charts-container">
                <div class="chart-wrapper">
                    <canvas id="marketChangesChart"></canvas>
                </div>
                <div class="chart-wrapper">
                    <canvas id="successRateChart"></canvas>
                </div>
            </div>
            
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th>Avg Market Change (%)</th>
                            <th>Max Market Change (%)</th>
                            <th>Median Market Change (%)</th>
                            <th>Min Market Change (%)</th>
                            <th>Positive Months</th>
                            <th>Success Rate (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {market_table_html}
                    </tbody>
                </table>
            </div>
        </div>
        """
    else:
        html += f"""
        <div class="card">
            <div class="empty-state">
                <i class="fas fa-chart-line"></i>
                <h3>No Market Data Available</h3>
                <p>We're unable to retrieve market data at this time. Please try again later.</p>
            </div>
        </div>
        """

    html += """
    <style>
        .empty-state {
            text-align: center;
            padding: 2rem;
            color: var(--text);
        }

        .empty-state i {
            font-size: 3rem;
            color: var(--border);
            margin-bottom: 1rem;
        }

        .empty-state h3 {
            margin: 0.5rem 0;
            color: var(--primary-color);
        }

        .empty-state p {
            color: var(--text);
            opacity: 0.8;
        }

        .charts-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }

        .chart-wrapper {
            background: var(--background);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .table-responsive {
            overflow-x: auto;
        }

        .positive { color: #28a745; }
        .negative { color: #dc3545; }

        @media (max-width: 768px) {
            .charts-container {
                grid-template-columns: 1fr;
            }
        }
        
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .alert-error {
            background-color: rgba(220, 53, 69, 0.1);
            color: #dc3545;
            border: 1px solid rgba(220, 53, 69, 0.2);
        }
    </style>
    """
    
    if market_data:
        months_json = json.dumps(months)
        avg_changes_json = json.dumps(avg_changes)
        success_rates_json = json.dumps(success_rates)
        bg_colors_json = json.dumps(bg_colors)
        border_colors_json = json.dumps(border_colors)
        
        html += f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                // Market Changes Chart
                const marketCtx = document.getElementById('marketChangesChart').getContext('2d');
                new Chart(marketCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {months_json},
                        datasets: [{{
                            label: 'Average Market Change (%)',
                            data: {avg_changes_json},
                            backgroundColor: {bg_colors_json},
                            borderColor: {border_colors_json},
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'Monthly Market Returns',
                                color: 'var(--text)'
                            }},
                            legend: {{
                                labels: {{
                                    color: 'var(--text)'
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                grid: {{
                                    color: 'var(--border)'
                                }},
                                ticks: {{
                                    color: 'var(--text)'
                                }}
                            }},
                            x: {{
                                grid: {{
                                    color: 'var(--border)'
                                }},
                                ticks: {{
                                    color: 'var(--text)'
                                }}
                            }}
                        }}
                    }}
                }});

                // Success Rate Chart
                const successCtx = document.getElementById('successRateChart').getContext('2d');
                new Chart(successCtx, {{
                    type: 'line',
                    data: {{
                        labels: {months_json},
                        datasets: [{{
                            label: 'Market Success Rate (%)',
                            data: {success_rates_json},
                            borderColor: 'rgb(74, 144, 226)',
                            backgroundColor: 'rgba(74, 144, 226, 0.1)',
                            fill: true,
                            tension: 0.4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'Monthly Market Success Rate',
                                color: 'var(--text)'
                            }},
                            legend: {{
                                labels: {{
                                    color: 'var(--text)'
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100,
                                grid: {{
                                    color: 'var(--border)'
                                }},
                                ticks: {{
                                    color: 'var(--text)'
                                }}
                            }},
                            x: {{
                                grid: {{
                                    color: 'var(--border)'
                                }},
                                ticks: {{
                                    color: 'var(--text)'
                                }}
                            }}
                        }}
                    }}
                }});
            }});
        </script>
        """
    
    return render_template_string(html) 