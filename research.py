import json
from flask import Blueprint, render_template_string
from common import get_api_data, get_live_stock_price, MENU_BAR, INST_LIST_API_URL, INST_HOLDINGS_API_URL

research_bp = Blueprint('research', __name__, url_prefix='/research')

@research_bp.route('/')
def research():
    inst_data = get_api_data(INST_LIST_API_URL)
    if "error" in inst_data:
        html = f"""
        <h1>Research</h1>
        {MENU_BAR}
        <p>Error fetching institution list: {inst_data['error']}</p>
        """
        return render_template_string(html)

    institutions = inst_data.get("data", [])
    holdings_master = {}
    inst_totals = {}

    for inst in institutions:
        name = inst if isinstance(inst, str) else inst.get('name', 'N/A')
        holdings_data = get_api_data(INST_HOLDINGS_API_URL.format(name=name))
        if "error" not in holdings_data:
            holdings = holdings_data.get("data", [])
            total_units = 0
            for holding in holdings:
                ticker = holding.get("ticker")
                units = float(holding.get("units", 0) or 0)
                total_units += units
                if ticker:
                    if ticker not in holdings_master:
                        holdings_master[ticker] = {}
                    holdings_master[ticker][name] = units
            inst_totals[name] = total_units

    inst_names = sorted(inst_totals.keys(), key=lambda x: inst_totals[x], reverse=True)[:10]

    table_html = "<table border='1' id='masterTable'><tr><th>Ticker</th><th>Total Units</th><th>Live Stock Price</th>"
    for name in inst_names:
        table_html += f"<th>{name}</th>"
    table_html += "</tr>"

    ticker_options = ""
    for ticker, inst_holdings in holdings_master.items():
        total_units = sum(inst_holdings.values())
        live_price = get_live_stock_price(ticker)
        table_html += f"<tr><td>{ticker}</td><td>{total_units}</td><td>{live_price if isinstance(live_price, (int, float)) else live_price}</td>"
        for name in inst_names:
            units = inst_holdings.get(name, 0)
            percentage = (units / total_units * 100) if total_units > 0 else 0
            table_html += f"<td>{percentage:.1f}%</td>"
        table_html += "</tr>"
        ticker_options += f"<option value='{ticker}'>{ticker}</option>"

    pie_chart_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <select id="institutionSelect" onchange="updatePieChart()">
        <option value="">Select an Institution</option>
    """
    for name in inst_names:
        pie_chart_html += f"<option value='{name}'>{name}</option>"
    pie_chart_html += """
    </select>
    <div id="pieChartContainer" style="display: none;">
        <button onclick="closePieChart()">Close</button>
        <canvas id="holdingsPieChart" width="400" height="400"></canvas>
    </div>
    <script>
        const holdingsDataMaster = {json.dumps(holdings_master)};
        let pieChart;

        function updatePieChart() {
            const institution = document.getElementById('institutionSelect').value;
            if (!institution) return;

            const holdings = {};
            for (let ticker in holdingsDataMaster) {
                if (holdingsDataMaster[ticker][institution]) {
                    holdings[ticker] = holdingsDataMaster[ticker][institution];
                }
            }
            const labels = Object.keys(holdings);
            const data = Object.values(holdings);

            if (pieChart) pieChart.destroy();
            const ctx = document.getElementById('holdingsPieChart').getContext('2d');
            pieChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
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
                        title: { display: true, text: `Holdings Distribution for ${institution}` }
                    }
                }
            });
            document.getElementById('pieChartContainer').style.display = 'block';
        }

        function closePieChart() {
            document.getElementById('pieChartContainer').style.display = 'none';
            document.getElementById('institutionSelect').value = '';
            if (pieChart) pieChart.destroy();
        }
    </script>
    """

    html = f"""
    <h1>Research</h1>
    {MENU_BAR}
    <h2>All Institution Holdings</h2>
    {table_html}
    <h2>Top 10 Holdings by Institution</h2>
    {pie_chart_html}
    """
    return render_template_string(html)
