from flask import Blueprint, render_template_string
from common import get_api_data, get_live_stock_price, MENU_BAR

institution_bp = Blueprint('institution', __name__, url_prefix='/')

@institution_bp.route('/')
def home():
    html = f"""
    <h1>Unusual Whales Dashboard</h1>
    {MENU_BAR}
    <p>Welcome to the Unusual Whales Dashboard. Select a page from the menu above.</p>
    """
    return render_template_string(html)

@institution_bp.route('/institution/list')
def institution_list():
    data = get_api_data(INST_LIST_API_URL)
    html = f"""
    <h1>Institution List</h1>
    {MENU_BAR}
    <style>
        .inst-table {{ transition: all 0.5s ease; }}
        .holdings-table {{ display: none; transition: all 0.5s ease; }}
        .show {{ display: block; }}
        .hide {{ display: none; }}
        .pie-chart-container {{ display: none; transition: all 0.5s ease; }}
    </style>
    <div id="instContainer">
        <table border='1' class='inst-table' id='instTable'>
            <tr><th>Name</th><th>Live Price</th><th>Chart</th></tr>
    """
    if "error" not in data:
        institutions = data.get("data", []) if isinstance(data, dict) else data
        for inst in institutions:
            name = inst if isinstance(inst, str) else inst.get('name', 'N/A')
            html += f"<tr><td><a href='#' onclick='showHoldings(\"{name}\")'>{name}</a></td><td>{get_live_stock_price(name) if name.isupper() else 'N/A'}</td><td><a href='#' onclick='showPieChart(\"{name}\")'>View Chart</a></td></tr>"
    else:
        html += f"<tr><td colspan='3'>Error: {data['error']}</td></tr>"
    html += """
        </table>
        <div id="holdingsContainer" class="holdings-table">
            <button onclick="closeHoldings()">Close</button>
            <table border='1' id='holdingsTable'></table>
        </div>
        <div id="pieChartContainer" class="pie-chart-container">
            <button onclick="closePieChart()">Close</button>
            <canvas id="holdingsPieChart" width="400" height="400"></canvas>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        function showHoldings(name) {
            fetch(`/institution/holdings?name=${encodeURIComponent(name)}`)
                .then(response => response.json())
                .then(data => {
                    let table = '<tr><th>Ticker</th><th>Units</th><th>Value</th><th>Live Price</th></tr>';
                    if (data.data) {
                        data.data.forEach(holding => {
                            table += '<tr><td>' + (holding.ticker || 'N/A') + '</td><td>' + 
                                    (holding.units || 'N/A') + '</td><td>' + 
                                    (holding.value || 'N/A') + '</td><td>' + 
                                    (get_live_stock_price(holding.ticker) || 'N/A') + '</td></tr>';
                        });
                    }
                    document.getElementById('holdingsTable').innerHTML = table;
                    document.getElementById('instTable').classList.add('hide');
                    document.getElementById('holdingsContainer').classList.add('show');
                    document.getElementById('pieChartContainer').classList.remove('show');
                })
                .catch(error => console.error('Error:', error));
        }
        function closeHoldings() {
            document.getElementById('instTable').classList.remove('hide');
            document.getElementById('holdingsContainer').classList.remove('show');
        }

        function showPieChart(name) {
            fetch(`/institution/holdings?name=${encodeURIComponent(name)}`)
                .then(response => response.json())
                .then(data => {
                    let holdings = {};
                    if (data.data) {
                        data.data.forEach(holding => {
                            holdings[holding.ticker || 'N/A'] = parseFloat(holding.units || 0);
                        });
                    }
                    const labels = Object.keys(holdings);
                    const dataValues = Object.values(holdings);

                    if (pieChart) pieChart.destroy();
                    const ctx = document.getElementById('holdingsPieChart').getContext('2d');
                    pieChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: labels,
                            datasets: [{
                                data: dataValues,
                                backgroundColor: [
                                    'rgba(255, 99, 132, 0.7)',
                                    'rgba(54, 162, 235, 0.7)',
                                    'rgba(255, 206, 86, 0.7)',
                                    'rgba(75, 192, 192, 0.7)',
                                    'rgba(153, 102, 255, 0.7)',
                                    'rgba(255, 159, 64, 0.7)'
                                ]
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: true,
                            plugins: {
                                legend: { position: 'right' },
                                title: { display: true, text: `Holdings Distribution for ${name}` }
                            }
                        }
                    });
                    document.getElementById('instTable').classList.add('hide');
                    document.getElementById('holdingsContainer').classList.remove('show');
                    document.getElementById('pieChartContainer').classList.add('show');
                })
                .catch(error => console.error('Error:', error));
        }

        function closePieChart() {
            document.getElementById('instTable').classList.remove('hide');
            document.getElementById('pieChartContainer').classList.remove('show');
        }

        let pieChart;
    </script>
    """
    return render_template_string(html)

@institution_bp.route('/institution/holdings')
def get_institution_holdings():
    from common import INST_HOLDINGS_API_URL, get_api_data
    name = request.args.get('name')
    data = get_api_data(INST_HOLDINGS_API_URL.format(name=name))
    return jsonify(data)
