from flask import Blueprint, render_template_string, request, jsonify
from common import get_api_data, MENU_BAR
import logging
import json
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URL for Market Spike
MARKET_SPIKE_API_URL = "https://api.unusualwhales.com/api/market/spike"

market_spike_bp = Blueprint('market_spike', __name__, url_prefix='/')

@market_spike_bp.route('/market-spike')
def market_spike():
    spike_data = None
    error = None
    
    # Get time range from query parameters (default to 'day')
    time_range = request.args.get('range', 'day')
    valid_ranges = ['hour', 'day', 'week', 'month']
    if time_range not in valid_ranges:
        time_range = 'day'
    
    try:
        # For testing, always generate mock data instead of making actual API calls
        spike_data = generate_mock_spike_data(time_range)
        
        # In a production environment, you would uncomment this code to use the real API
        # response = get_api_data(MARKET_SPIKE_API_URL)
        # if "error" not in response:
        #     spike_data = response.get("data", [])
        #     # If no data is returned, generate mock data for testing
        #     if not spike_data:
        #         spike_data = generate_mock_spike_data(time_range)
        # else:
        #     error = response.get("error", "Failed to retrieve market spike data")
        #     # Generate mock data for testing if there's an error
        #     spike_data = generate_mock_spike_data(time_range)
    except Exception as e:
        error = str(e)
        logger.error(f"Error processing market spike data: {str(e)}")
        # Generate mock data for testing if there's an exception
        spike_data = generate_mock_spike_data(time_range)
    
    # Prepare data for chart
    chart_data = prepare_chart_data(spike_data)
    
    html = """
    {{ style }}
    <div class="container">
        <h1>Market Spike</h1>
        """ + MENU_BAR + """
        
        <div class="card">
            <div class="card-header">
                <h2><i class="fas fa-bolt"></i> Market Spike Analysis</h2>
                <div class="range-selector">
                    <a href="/market-spike?range=hour" class="btn btn-sm {{ 'active' if range == 'hour' else '' }}">Hour</a>
                    <a href="/market-spike?range=day" class="btn btn-sm {{ 'active' if range == 'day' else '' }}">Day</a>
                    <a href="/market-spike?range=week" class="btn btn-sm {{ 'active' if range == 'week' else '' }}">Week</a>
                    <a href="/market-spike?range=month" class="btn btn-sm {{ 'active' if range == 'month' else '' }}">Month</a>
                </div>
            </div>
            
            <div class="spike-chart-wrapper">
                <div class="spike-chart-container">
                    <canvas id="spikeChart"></canvas>
                </div>
            </div>
    """
    
    if error:
        html += f"""
        <div class="alert alert-error">
            <i class="fas fa-exclamation-circle"></i>
            {error}
        </div>
        """
    
    html += """
            <div class="spike-info-cards">
                <div class="info-card">
                    <div class="info-card-header">
                        <i class="fas fa-chart-line"></i>
                        <h3>Current Spike Value</h3>
                    </div>
                    <div class="info-card-body">
                        <span class="value">{{ current_value }}</span>
                    </div>
                </div>
                
                <div class="info-card">
                    <div class="info-card-header">
                        <i class="fas fa-arrow-up"></i>
                        <h3>Max Spike</h3>
                    </div>
                    <div class="info-card-body">
                        <span class="value">{{ max_value }}</span>
                        <span class="time">{{ max_time }}</span>
                    </div>
                </div>
                
                <div class="info-card">
                    <div class="info-card-header">
                        <i class="fas fa-arrow-down"></i>
                        <h3>Min Spike</h3>
                    </div>
                    <div class="info-card-body">
                        <span class="value">{{ min_value }}</span>
                        <span class="time">{{ min_time }}</span>
                    </div>
                </div>
            </div>
            
            <div class="spike-data-table">
                <h3>Recent Spike Data</h3>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Value</th>
                                <th>Change</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    # Add table rows for recent spike data (last 10 entries)
    if spike_data:
        recent_data = spike_data[-10:] if len(spike_data) > 10 else spike_data
        prev_value = None
        
        for item in reversed(recent_data):
            time_str = item.get('time', '')
            value = float(item.get('value', 0))
            
            # Format time
            try:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M:%S')
            except:
                formatted_time = time_str
            
            # Calculate change
            change = 0
            change_class = ''
            change_icon = ''
            
            if prev_value is not None:
                change = value - prev_value
                change_class = 'positive' if change >= 0 else 'negative'
                change_icon = 'caret-up' if change >= 0 else 'caret-down'
            
            prev_value = value
            
            html += f"""
                            <tr>
                                <td>{formatted_time}</td>
                                <td>{value:.2f}</td>
                                <td class="{change_class}">
                                    {f'<i class="fas fa-{change_icon}"></i> {abs(change):.2f}' if prev_value is not None else '-'}
                                </td>
                            </tr>
            """
    
    html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <style>
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .range-selector {
            display: flex;
            gap: 0.5rem;
        }
        
        .btn-sm {
            padding: 0.3rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        .range-selector .btn {
            background-color: var(--background);
            color: var(--text);
            border: 1px solid var(--border);
            transition: all 0.2s ease;
        }
        
        .range-selector .btn:hover {
            background-color: var(--hover);
        }
        
        .range-selector .btn.active {
            background-color: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        .spike-chart-wrapper {
            position: relative;
            width: 100%;
            padding-bottom: 0;
            margin-bottom: 1.5rem;
        }
        
        .spike-chart-container {
            width: 100%;
            height: 350px;
            background-color: var(--background);
            border-radius: 8px;
            padding: 1rem;
            position: relative;
            overflow: hidden;
            border: 1px solid var(--border);
        }
        
        .spike-info-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .info-card {
            background-color: var(--background);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .info-card-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }
        
        .info-card-header i {
            color: var(--primary-color);
            font-size: 1.2rem;
        }
        
        .info-card-header h3 {
            margin: 0;
            font-size: 1rem;
            color: var(--text);
        }
        
        .info-card-body {
            display: flex;
            flex-direction: column;
        }
        
        .info-card-body .value {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .info-card-body .time {
            font-size: 0.8rem;
            color: var(--text);
            opacity: 0.7;
        }
        
        .spike-data-table {
            margin-top: 1.5rem;
        }
        
        .spike-data-table h3 {
            margin-bottom: 1rem;
            font-size: 1.2rem;
            color: var(--text);
        }
        
        .table-responsive {
            overflow-x: auto;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .table-responsive table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .table-responsive th, 
        .table-responsive td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        
        .table-responsive th {
            background-color: var(--background);
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 2px solid var(--border);
        }
        
        .positive { 
            color: #28a745; 
        }
        
        .negative { 
            color: #dc3545; 
        }
        
        .alert {
            padding: 0.75rem;
            border-radius: 8px;
            margin: 0.75rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }
        
        .alert-error {
            background-color: rgba(220, 53, 69, 0.1);
            color: #dc3545;
            border: 1px solid rgba(220, 53, 69, 0.2);
        }
        
        @media (max-width: 768px) {
            .card-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            
            .range-selector {
                width: 100%;
                justify-content: space-between;
            }
            
            .spike-chart-container {
                height: 300px;
            }
            
            .spike-info-cards {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """
    
    # Add Chart.js script if we have data
    if chart_data:
        times_json = json.dumps(chart_data.get('times', []))
        values_json = json.dumps(chart_data.get('values', []))
        
        html += f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const ctx = document.getElementById('spikeChart').getContext('2d');
                
                // Create gradient
                const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                gradient.addColorStop(0, 'rgba(74, 144, 226, 0.5)');
                gradient.addColorStop(1, 'rgba(74, 144, 226, 0.0)');
                
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {times_json},
                        datasets: [{{
                            label: 'Spike Value',
                            data: {values_json},
                            borderColor: 'rgb(74, 144, 226)',
                            backgroundColor: gradient,
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true,
                            pointRadius: 2,
                            pointHoverRadius: 5,
                            pointBackgroundColor: 'rgb(74, 144, 226)'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{
                            mode: 'index',
                            intersect: false,
                        }},
                        layout: {{
                            padding: {{
                                left: 10,
                                right: 10,
                                top: 20,
                                bottom: 10
                            }}
                        }},
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'top',
                                labels: {{
                                    boxWidth: 12,
                                    padding: 10,
                                    font: {{
                                        size: 11
                                    }}
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                titleFont: {{
                                    size: 12
                                }},
                                bodyFont: {{
                                    size: 11
                                }},
                                padding: 10,
                                displayColors: true,
                                callbacks: {{
                                    label: function(context) {{
                                        let value = context.raw;
                                        return `Value: ${{value.toFixed(2)}}`;
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                grid: {{
                                    color: 'rgba(0, 0, 0, 0.05)'
                                }},
                                ticks: {{
                                    maxRotation: 0,
                                    autoSkip: true,
                                    maxTicksLimit: 12,
                                    font: {{
                                        size: 10
                                    }}
                                }}
                            }},
                            y: {{
                                beginAtZero: false,
                                grid: {{
                                    color: 'rgba(0, 0, 0, 0.05)'
                                }},
                                ticks: {{
                                    callback: function(value) {{
                                        return value.toFixed(2);
                                    }},
                                    font: {{
                                        size: 10
                                    }},
                                    maxTicksLimit: 8
                                }}
                            }}
                        }}
                    }}
                }});
            }});
        </script>
        """
    
    # Calculate statistics for display
    current_value = "N/A"
    max_value = "N/A"
    min_value = "N/A"
    max_time = "N/A"
    min_time = "N/A"
    
    if spike_data:
        # Current value (most recent)
        current_value = f"{float(spike_data[-1].get('value', 0)):.2f}"
        
        # Find max and min values
        max_val = float(spike_data[0].get('value', 0))
        min_val = float(spike_data[0].get('value', 0))
        max_idx = 0
        min_idx = 0
        
        for i, item in enumerate(spike_data):
            val = float(item.get('value', 0))
            if val > max_val:
                max_val = val
                max_idx = i
            if val < min_val:
                min_val = val
                min_idx = i
        
        max_value = f"{max_val:.2f}"
        min_value = f"{min_val:.2f}"
        
        # Format times
        try:
            max_dt = datetime.fromisoformat(spike_data[max_idx].get('time', '').replace('Z', '+00:00'))
            max_time = max_dt.strftime('%H:%M:%S')
        except:
            max_time = spike_data[max_idx].get('time', '')
            
        try:
            min_dt = datetime.fromisoformat(spike_data[min_idx].get('time', '').replace('Z', '+00:00'))
            min_time = min_dt.strftime('%H:%M:%S')
        except:
            min_time = spike_data[min_idx].get('time', '')
    
    return render_template_string(html, 
                                 range=time_range,
                                 current_value=current_value,
                                 max_value=max_value,
                                 min_value=min_value,
                                 max_time=max_time,
                                 min_time=min_time)

def generate_mock_spike_data(time_range):
    """Generate mock spike data for testing"""
    data = []
    now = datetime.now()
    
    # Determine number of data points and time interval based on range
    if time_range == 'hour':
        num_points = 60  # 1 minute intervals
        interval = timedelta(minutes=1)
        start_time = now - timedelta(minutes=59)
    elif time_range == 'day':
        num_points = 24 * 6  # 10 minute intervals
        interval = timedelta(minutes=10)
        start_time = now - timedelta(days=1) + timedelta(minutes=10)
    elif time_range == 'week':
        num_points = 7 * 24  # 1 hour intervals
        interval = timedelta(hours=1)
        start_time = now - timedelta(days=7) + timedelta(hours=1)
    else:  # month
        num_points = 30  # 1 day intervals
        interval = timedelta(days=1)
        start_time = now - timedelta(days=29)
    
    # Generate base value and trend
    base_value = 20.0
    trend = 0.05  # Slight upward trend
    
    # Generate data points
    for i in range(num_points):
        time_point = start_time + interval * i
        
        # Add randomness but keep a general trend
        noise = random.uniform(-0.5, 0.5)
        trend_component = trend * (i / num_points)
        
        # Add some volatility
        volatility = 0.2
        if random.random() < 0.1:  # 10% chance of a spike
            volatility = random.uniform(0.5, 1.5)
        
        # Calculate value
        value = base_value + trend_component + noise * volatility
        
        # Add to data
        data.append({
            'time': time_point.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'value': f"{value:.2f}"
        })
    
    return data

def prepare_chart_data(spike_data):
    """Prepare data for Chart.js"""
    if not spike_data:
        return None
    
    times = []
    values = []
    
    for item in spike_data:
        # Format time for display
        time_str = item.get('time', '')
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%H:%M')
        except:
            formatted_time = time_str
        
        times.append(formatted_time)
        values.append(float(item.get('value', 0)))
    
    return {
        'times': times,
        'values': values
    } 