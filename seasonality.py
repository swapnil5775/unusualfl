from flask import Blueprint, render_template_string, request, jsonify
from common import get_api_data, get_live_stock_price, MENU_BAR, SEASONALITY_API_URL, SEASONALITY_MARKET_API_URL, ETF_INFO_API_URL, OPENAI_API_KEY
import logging
import json
import openai
import yfinance as yf
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenAI API
openai.api_key = OPENAI_API_KEY

seasonality_bp = Blueprint('seasonality', __name__, url_prefix='/')

@seasonality_bp.route('/seasonality')
def seasonality():
    # [Landing page HTML]
    return render_template_string(html)

@seasonality_bp.route('/seasonality/per-ticker', methods=['GET'])
def seasonality_per_ticker():
    # [Per-ticker seasonality logic with tables and charts]
    return render_template_string(html, **context)

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(seasonality_bp)
    app.run(debug=True)
