from flask import Blueprint, render_template_string, request, jsonify
from common import get_api_data, get_live_stock_price, MENU_BAR, SEASONALITY_MARKET_API_URL, OPENAI_API_KEY
import logging
import json
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenAI API
openai.api_key = OPENAI_API_KEY

seasonality_etf_bp = Blueprint('seasonality_etf', __name__, url_prefix='/seasonality/etf-market')

@seasonality_etf_bp.route('/', methods=['GET'])
def seasonality_etf_market():
    ticker = request.args.get('ticker', 'ALL').upper()
    data = None
    error = None

    response = get_api_data(SEASONALITY_MARKET_API_URL)
    if "error" in response:
        error = response["error"]
        logger.error(f"API Error for {SEASONALITY_MARKET_API_URL}: {error}")
    else:
        all_data = response.get("data", [])
        data = [item for item in all_data if item['ticker'] == ticker] if ticker != 'ALL' else all_data

    etf_tickers = ['SPY', 'QQQ', 'IWM', 'XLE', 'XLC', 'XLK', 'XLV', 'XLP', 'XLY', 'XLRE', 'XLF', 'XLI', 'XLB']

    # Prepare context for Jinja2 templating
    context = {
        'ticker': ticker,
        'data': data,
        'error': error,
        'etf_tickers': etf_tickers,
        'MENU_BAR': MENU_BAR
    }

    html = """
    <h1>Seasonality - ETF Market</h1>
    {{ MENU_BAR | safe }}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 2; min-width: 300px; margin-right: 20px;">
            <h3>Select ETF or View All:</h3>
            <div>
                <button onclick="window.location.href='/seasonality/etf-market?ticker=ALL'">ALL</button>
    """
    for t in etf_tickers:
        html += f"""
            <button onclick="window.location.href='/seasonality/etf-market?ticker={t}'">{t}</button>
        """
    html += """
            </div>
            {% if error %}<p style="color: red;">Error: {{ error }}</p>{% endif %}
            {% if not error and not data %}<p>No data available for ticker {{ ticker }}</p>{% endif %}
            <table border='1' {% if not data %}style="display: none;"{% endif %} id="etfMarketTable">
                <tr>
                    <th><a href="#" onclick="sortTable('ticker')">Ticker</a></th>
                    <th><a href="#" onclick="sortTable('month')">Month</a></th>
                    <th><a href="#" onclick="sortTable('avg_change')">Avg Change</a></th>
                    <th><a href="#" onclick="sortTable('max_change')">Max Change</a></th>
                    <th><a href="#" onclick="sortTable('median_change')">Median Change</a></th>
                    <th><a href="#" onclick="sortTable('min_change')">Min Change</a></th>
                    <th><a href="#" onclick="sortTable('positive_closes')">Positive Closes</a></th>
                    <th><a href="#" onclick="sortTable('positive_months_perc')">Positive Months %</a></th>
                    <th><a href="#" onclick="sortTable('years')">Years</a></th>
                    <th>Live Price</th>
                </tr>
    """
    if data:
        for item in data:
            avg_change = float(item.get('avg_change', 0.0)) if item.get('avg_change') else 0.0
            max_change = float(item.get('max_change', 0.0)) if item.get('max_change') else 0.0
            median_change = float(item.get('median_change', 0.0)) if item.get('median_change') else 0.0
            min_change = float(item.get('min_change', 0.0)) if item.get('min_change') else 0.0
            positive_months_perc = float(item.get('positive_months_perc', 0.0)) * 100
            positive_closes = item.get('positive_closes', 0)
            years = item.get('years', 'N/A')
            month = item.get('month', 'N/A')
            ticker_val = item.get('ticker', 'N/A')
            live_price = get_live_stock_price(ticker_val) if ticker_val != 'N/A' else 'N/A'

            def format_with_color(value, decimals=2):
                color = 'red' if value < 0 else 'black'
                return f'<span style="color: {color}">{value:.{decimals}f}</span>'

            html += f"""
            <tr>
                <td>{ticker_val}</td>
                <td>{month}</td>
                <td>{format_with_color(avg_change)}</td>
                <td>{format_with_color(max_change)}</td>
                <td>{format_with_color(median_change)}</td>
                <td>{format_with_color(min_change)}</td>
                <td>{positive_closes}</td>
                <td>{positive_months_perc:.2f}%</td>
                <td>{years}</td>
                <td>{live_price if isinstance(live_price, (int, float)) else live_price}</td>
            </tr>
            """

    html += """
            </table>
        </div>
        <div style="flex: 1; min-width: 300px; padding: 20px; border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9;">
            <h3>AI Summary</h3>
            <textarea id="aiQuestion" rows="4" cols="50" placeholder="Enter your question about the ETF seasonality data..."></textarea>
            <br>
            <button onclick="getAiSummary()">Run AI Summary</button>
            <div id="aiResponse" style="margin-top: 10px;"></div>
        </div>
    </div>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        let sortState = { col: 'ticker', dir: 'asc' };

        function sortTable(col) {
            const newDir = sortState.col === col && sortState.dir === 'asc' ? 'desc' : 'asc';
            sortState = { col: col, dir: newDir };
            window.location.href = `/seasonality/etf-market?ticker={{ ticker if ticker != 'ALL' else 'ALL' }}&sort_col=${col}&sort_dir=${newDir}`;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const sortCol = urlParams.get('sort_col');
        const sortDir = urlParams.get('sort_dir');
        if (sortCol && sortDir) {
            sortState.col = sortCol;
            sortState.dir = sortDir;
        }

        async function getAiSummary() {
            const question = document.getElementById('aiQuestion').value;
            if (!question) {
                alert('Please enter a question.');
                return;
            }

            const data = {{ data | tojson | safe }};
            if (!data || data.length === 0) {
                document.getElementById('aiResponse').innerHTML = '<p>No data available for analysis.</p>';
                return;
            }

            // Convert data to CSV-like format for OpenAI
            const csvData = data.map(item => `
                Month: ${item.month}, ETF: ${item.ticker}, Avg Change: ${item.avg_change}, 
                Positive Months %: ${item.positive_months_perc * 100}`).join('\n');

            try {
                const response = await fetch('/api/ai-summary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question, data: csvData })
                });
                const result = await response.json();
                document.getElementById('aiResponse').innerHTML = '<ul>' + result.summary.map(point => `<li>${point}</li>`).join('') + '</ul>';
            } catch (error) {
                document.getElementById('aiResponse').innerHTML = `<p>Error: ${error.message}</p>`;
            }
        }
    </script>
    """

    return render_template_string(html, **context)

# Define the Flask app instance for this blueprint
app = Flask(__name__)
app.register_blueprint(seasonality_etf_bp)

@app.route('/api/ai-summary', methods=['POST'])
def ai_summary():
    data = request.json
    question = data.get('question', '')
    csv_data = data.get('data', '')

    prompt = f"""
    Analyze the given ETF seasonality data and generate a structured response with 4 bullet points of unique insights based on the following prompt:

    - Analyze the given ETF seasonality data and generate a structured table with the following columns:
      1. Month (Display as full month name instead of a number)
      2. ETF (The ETF ticker symbol)
      3. Upside/Downside Change (The average price change for that ETF in that month)
      4. Insight (A brief explanation of why the ETF should be watched in that month)
      5. Win Probability (%) (Percentage of months in the last 15 years where the ETF closed positively)

    Ensure the response provides actionable insights, helping users understand which ETFs to monitor for potential upside or downside movements based on historical trends.

    Data:
    {csv_data}

    Question: {question}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # You can use "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a financial data analyst specializing in ETF seasonality trends."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        summary = response.choices[0].message['content'].strip().split('\n')
        summary = [line.strip('- ').strip() for line in summary if line.strip()]
        return jsonify({"summary": summary[:4]})  # Limit to 4 bullet points
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
