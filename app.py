from flask import Flask, render_template_string, request, send_from_directory
import os
import ssl
from institution_list import institution_bp
from research import research_bp
from seasonality import seasonality_bp
from etf_research import etf_research_bp
from etf_market import etf_market_bp
from market_tide import market_tide_bp
from market_spike import market_spike_bp
from flow_per_strike import flow_per_strike_bp
from common import MENU_BAR
from insider_trades import insider_trades_bp
from congress_trades import congress_trades_bp
from premium_options import premium_options_bp
from most_active_stocks import most_active_bp
from market_movers import market_movers_bp

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Create a custom SSL context that doesn't verify certificates globally
ssl._create_default_https_context = ssl._create_unverified_context

# Configure error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template_string(f"""
        {{ style }}
        <div class="container">
            <h1>Page Not Found</h1>
            {MENU_BAR}
            <div class="error-card">
                <i class="fas fa-exclamation-circle"></i>
                <p>The requested page could not be found.</p>
                <a href="/" class="btn">Go Home</a>
            </div>
        </div>
    """), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template_string(f"""
        {{ style }}
        <div class="container">
            <h1>Internal Server Error</h1>
            {MENU_BAR}
            <div class="error-card">
                <i class="fas fa-exclamation-triangle"></i>
                <p>An internal server error occurred. Please try again later.</p>
                <a href="/" class="btn">Go Home</a>
            </div>
        </div>
    """), 500

# Register blueprints
app.register_blueprint(institution_bp)
app.register_blueprint(research_bp)
app.register_blueprint(seasonality_bp)
app.register_blueprint(etf_research_bp)
app.register_blueprint(etf_market_bp)
app.register_blueprint(market_tide_bp)
app.register_blueprint(market_spike_bp)
app.register_blueprint(flow_per_strike_bp)
app.register_blueprint(insider_trades_bp)
app.register_blueprint(congress_trades_bp)
app.register_blueprint(premium_options_bp)
app.register_blueprint(most_active_bp)
app.register_blueprint(market_movers_bp)

# Create static folder if it doesn't exist
os.makedirs('static', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Create CSS file
with open('static/css/style.css', 'w') as f:
    f.write("""
:root {
    --primary-color: #0066cc;
    --primary-rgb: 0, 102, 204;
    --secondary-color: #4a90e2;
    --background-light: #ffffff;
    --text-light: #333333;
    --text-secondary-light: #666666;
    --border-light: #e0e0e0;
    --hover-light: #f5f5f5;
    --background-dark: #1a1a1a;
    --text-dark: #f0f0f0;
    --text-secondary-dark: #bbbbbb;
    --border-dark: #333333;
    --hover-dark: #2a2a2a;
    --accent-color: #ff9900;
}

[data-theme="dark"] {
    --background: var(--background-dark);
    --text: var(--text-dark);
    --text-secondary: var(--text-secondary-dark);
    --border: var(--border-dark);
    --hover: var(--hover-dark);
}

[data-theme="light"] {
    --background: var(--background-light);
    --text: var(--text-light);
    --text-secondary: var(--text-secondary-light);
    --border: var(--border-light);
    --hover: var(--hover-light);
}

body { 
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    margin: 0;
    padding: 0;
    background-color: var(--background);
    color: var(--text);
    transition: all 0.3s ease;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    color: var(--primary-color);
    font-size: 2.5em;
    margin-bottom: 30px;
}

.card {
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
}

table {
    width: 100%;
    border-collapse: collapse;
    background: var(--background);
    margin: 20px 0;
    border-radius: 8px;
    overflow: hidden;
}

th, td {
    padding: 15px;
    text-align: left;
    border: 1px solid var(--border);
}

th {
    background-color: var(--primary-color);
    color: white;
}

tr:hover {
    background-color: var(--hover);
}

.btn {
    display: inline-block;
    padding: 10px 20px;
    background-color: var(--primary-color);
    color: white;
    text-decoration: none;
    border-radius: 5px;
    transition: background-color 0.2s ease;
}

.btn:hover {
    background-color: var(--secondary-color);
}

input[type="text"], select {
    padding: 10px;
    border: 1px solid var(--border);
    border-radius: 5px;
    margin-right: 10px;
    background: var(--background);
    color: var(--text);
}

canvas {
    background: var(--background);
    padding: 20px;
    border-radius: 8px;
    border: 1px solid var(--border);
}

.theme-switch {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
}

.error-card {
    text-align: center;
    padding: 40px;
    background: var(--background);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error-card i {
    font-size: 48px;
    color: var(--primary-color);
    margin-bottom: 20px;
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    table {
        display: block;
        overflow-x: auto;
    }
}
""")

# Create JS file
with open('static/js/theme.js', 'w') as f:
    f.write("""
// Set default theme if not already set
if (!localStorage.getItem('theme')) {
    localStorage.setItem('theme', 'light');
}

function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
});
""")

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Home page
@app.route('/')
def home():
    return render_template_string("""
        {{ style }}
        <div class="container">
            <h1>FinanceHub: Financial Market Analysis Tools</h1>
            """ + MENU_BAR + """
            
            <div class="features-grid">
                <div class="feature-card">
                    <i class="fas fa-building feature-icon"></i>
                    <h3>Institutional Holdings</h3>
                    <p>Explore what major institutions are buying and selling.</p>
                    <a href="/institution-list" class="btn">View Institutions</a>
                </div>
                
                <div class="feature-card">
                    <i class="fas fa-search feature-icon"></i>
                    <h3>Stock Research</h3>
                    <p>Detailed analysis and research for individual stocks.</p>
                    <a href="/research" class="btn">Research Stocks</a>
                </div>
                
                <div class="feature-card">
                    <i class="fas fa-calendar-alt feature-icon"></i>
                    <h3>Seasonality</h3>
                    <p>Analyze seasonal patterns in stock performance.</p>
                    <a href="/seasonality" class="btn">Check Seasonality</a>
                </div>
                
                <div class="feature-card">
                    <i class="fas fa-chart-pie feature-icon"></i>
                    <h3>ETF Research</h3>
                    <p>Research ETF holdings, performance, and flows.</p>
                    <a href="/etf-research" class="btn">Explore ETFs</a>
                </div>
                
                <div class="feature-card">
                    <i class="fas fa-dollar-sign feature-icon"></i>
                    <h3>Premium Options Trades</h3>
                    <p>Track high-value options trades in real-time.</p>
                    <a href="/premium-options" class="btn">Monitor Options</a>
                </div>
                
                <div class="feature-card">
                    <i class="fas fa-user-secret feature-icon"></i>
                    <h3>Insider Trading</h3>
                    <p>Track buying and selling from company insiders.</p>
                    <a href="/insider-trades" class="btn">View Insider Trades</a>
                </div>
                
                <div class="feature-card">
                    <i class="fas fa-fire feature-icon"></i>
                    <h3>Most Active Stocks</h3>
                    <p>Monitor the most actively traded stocks in the market.</p>
                    <a href="/most-active-stocks" class="btn">View Most Active</a>
                </div>
                
                <div class="feature-card">
                    <i class="fas fa-sort-amount-up feature-icon"></i>
                    <h3>Market Movers</h3>
                    <p>Track top gainers and losers in the market.</p>
                    <a href="/market-movers" class="btn">View Market Movers</a>
                </div>
            </div>
            
            <div class="intro-section">
                <h2>About FinanceHub</h2>
                <p>
                    FinanceHub provides powerful tools for investors and traders to analyze financial markets, 
                    track institutional activity, monitor options flow, and more. Our platform integrates 
                    data from multiple sources to give you the edge in today's fast-moving markets.
                </p>
            </div>
        </div>
        
        <style>
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            
            .feature-card {
                background: var(--background);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 25px;
                text-align: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            
            .feature-icon {
                font-size: 40px;
                color: var(--primary-color);
                margin-bottom: 15px;
            }
            
            .feature-card h3 {
                margin-bottom: 10px;
                color: var(--text);
            }
            
            .feature-card p {
                color: var(--text);
                opacity: 0.8;
                margin-bottom: 20px;
            }
            
            .intro-section {
                margin-top: 50px;
                padding: 30px;
                background: var(--background);
                border: 1px solid var(--border);
                border-radius: 8px;
            }
            
            .intro-section h2 {
                color: var(--primary-color);
                margin-bottom: 15px;
            }
            
            .intro-section p {
                line-height: 1.6;
                color: var(--text);
                opacity: 0.9;
            }
            
            @media (max-width: 768px) {
                .features-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    """)

# Add basic styling to all pages
@app.before_request
def before_request():
    app.jinja_env.globals.update(
        style="""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FinanceHub</title>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <link href="/static/css/style.css" rel="stylesheet">
            <script src="/static/js/theme.js"></script>
        </head>
        <body data-theme="light">
        """
    )
    # Add isinstance to the global template context
    app.jinja_env.globals.update(isinstance=isinstance)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
