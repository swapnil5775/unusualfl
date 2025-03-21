from flask import Blueprint, render_template_string, request, jsonify
import requests
import time
from datetime import datetime
from common import MENU_BAR

# Blueprint configuration
most_active_bp = Blueprint('most_active', __name__)

# Alpaca API credentials for paper trading
ALPACA_API_KEY = "AK49TL9A4OLPKO9PAUH3"
ALPACA_API_SECRET = "0744CcGjrhPXvsORtWJpSMNWpEYuDTegOlE0OgLV"

# Function to get the most active stocks data from Alpaca API
def get_most_active_stocks(top=10, metric="volume"):
    url = f"https://data.alpaca.markets/v1beta1/screener/stocks/most-actives?by={metric}&top={top}"
    
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching most active stocks: {e}")
        return {"error": str(e)}

# Route for Most Active Stocks page
@most_active_bp.route('/most-active-stocks')
def most_active_stocks():
    return render_template_string("""
        {{ style }}
        <div class="container">
            <h1>Most Active Stocks</h1>
            """ + MENU_BAR + """
            
            <div class="card">
                <div class="card-header">
                    <h2><i class="fas fa-fire"></i> Most Active Stocks by Volume</h2>
                    <div class="refresh-controls">
                        <span id="last-updated">Last Updated: <span id="update-time">Just Now</span></span>
                        <button id="refresh-btn" class="btn"><i class="fas fa-sync-alt"></i> Refresh Now</button>
                    </div>
                </div>
                
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Trade Count</th>
                                <th>Volume</th>
                            </tr>
                        </thead>
                        <tbody id="most-active-table">
                            <tr>
                                <td colspan="3" class="loading">Loading data...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <style>
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .refresh-controls {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            #last-updated {
                font-size: 0.9em;
                color: #666;
            }
            
            .loading {
                text-align: center;
                padding: 20px;
                color: #666;
                font-style: italic;
            }
            
            .table-container {
                overflow-x: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid var(--border);
            }
            
            th {
                background-color: var(--primary-color);
                color: white;
                font-weight: bold;
            }
            
            tbody tr:hover {
                background-color: var(--hover);
            }
            
            .up {
                color: #28a745;
            }
            
            .down {
                color: #dc3545;
            }
        </style>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const mostActiveTable = document.getElementById('most-active-table');
                const refreshBtn = document.getElementById('refresh-btn');
                const updateTimeEl = document.getElementById('update-time');
                
                let autoRefreshInterval = null;
                
                // Function to format large numbers with commas
                function formatNumber(num) {
                    return num.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, ",");
                }
                
                // Function to update the timestamp
                function updateTimestamp() {
                    const now = new Date();
                    const timeStr = now.toLocaleTimeString();
                    updateTimeEl.textContent = timeStr;
                }
                
                // Function to fetch and display data
                async function fetchData() {
                    try {
                        const response = await fetch('/most-active-stocks/data');
                        const data = await response.json();
                        
                        if (data.error) {
                            mostActiveTable.innerHTML = `
                                <tr>
                                    <td colspan="3" class="error">Error: ${data.error}</td>
                                </tr>
                            `;
                            return;
                        }
                        
                        const mostActives = data.most_actives || [];
                        
                        if (mostActives.length === 0) {
                            mostActiveTable.innerHTML = `
                                <tr>
                                    <td colspan="3" class="empty">No data available</td>
                                </tr>
                            `;
                            return;
                        }
                        
                        let tableHTML = '';
                        
                        mostActives.forEach(stock => {
                            tableHTML += `
                                <tr>
                                    <td>${stock.symbol}</td>
                                    <td>${formatNumber(stock.trade_count)}</td>
                                    <td>${formatNumber(stock.volume)}</td>
                                </tr>
                            `;
                        });
                        
                        mostActiveTable.innerHTML = tableHTML;
                        updateTimestamp();
                        
                    } catch (error) {
                        console.error('Error fetching data:', error);
                        mostActiveTable.innerHTML = `
                            <tr>
                                <td colspan="3" class="error">Error fetching data. Please try again.</td>
                            </tr>
                        `;
                    }
                }
                
                // Refresh button click handler
                refreshBtn.addEventListener('click', fetchData);
                
                // Set up auto-refresh every 30 seconds
                function startAutoRefresh() {
                    if (autoRefreshInterval) {
                        clearInterval(autoRefreshInterval);
                    }
                    
                    autoRefreshInterval = setInterval(fetchData, 30000);
                }
                
                // Initial data fetch
                fetchData();
                
                // Start auto-refresh
                startAutoRefresh();
            });
        </script>
    """)

# API endpoint to get most active stocks data
@most_active_bp.route('/most-active-stocks/data')
def get_most_active_data():
    data = get_most_active_stocks()
    return jsonify(data) 