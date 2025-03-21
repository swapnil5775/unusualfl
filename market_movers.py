from flask import Blueprint, render_template_string, request, jsonify
import requests
import time
from datetime import datetime
from common import MENU_BAR

# Blueprint configuration
market_movers_bp = Blueprint('market_movers', __name__)

# Alpaca API credentials for paper trading
ALPACA_API_KEY = "AK49TL9A4OLPKO9PAUH3"
ALPACA_API_SECRET = "0744CcGjrhPXvsORtWJpSMNWpEYuDTegOlE0OgLV"

# Function to get market movers data from Alpaca API
def get_market_movers(top=10):
    url = f"https://data.alpaca.markets/v1beta1/screener/stocks/movers?top={top}"
    
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
        print(f"Error fetching market movers: {e}")
        return {"error": str(e)}

# Route for Market Movers page
@market_movers_bp.route('/market-movers')
def market_movers():
    return render_template_string("""
        {{ style }}
        <div class="container">
            <h1>Top Market Movers</h1>
            """ + MENU_BAR + """
            
            <div class="grid-container">
                <div class="card">
                    <div class="card-header">
                        <h2><i class="fas fa-arrow-up"></i> Top Gainers</h2>
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
                                    <th>Price ($)</th>
                                    <th>Change ($)</th>
                                    <th>Change (%)</th>
                                </tr>
                            </thead>
                            <tbody id="gainers-table">
                                <tr>
                                    <td colspan="4" class="loading">Loading data...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2><i class="fas fa-arrow-down"></i> Top Losers</h2>
                    </div>
                    
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Price ($)</th>
                                    <th>Change ($)</th>
                                    <th>Change (%)</th>
                                </tr>
                            </thead>
                            <tbody id="losers-table">
                                <tr>
                                    <td colspan="4" class="loading">Loading data...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
            .grid-container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
                gap: 20px;
            }
            
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
            
            @media (max-width: 768px) {
                .grid-container {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const gainersTable = document.getElementById('gainers-table');
                const losersTable = document.getElementById('losers-table');
                const refreshBtn = document.getElementById('refresh-btn');
                const updateTimeEl = document.getElementById('update-time');
                
                let autoRefreshInterval = null;
                
                // Function to format numbers with 2 decimal places
                function formatNumber(num) {
                    return parseFloat(num).toFixed(2);
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
                        const response = await fetch('/market-movers/data');
                        const data = await response.json();
                        
                        if (data.error) {
                            gainersTable.innerHTML = `
                                <tr>
                                    <td colspan="4" class="error">Error: ${data.error}</td>
                                </tr>
                            `;
                            losersTable.innerHTML = `
                                <tr>
                                    <td colspan="4" class="error">Error: ${data.error}</td>
                                </tr>
                            `;
                            return;
                        }
                        
                        // Process gainers
                        const gainers = data.gainers || [];
                        if (gainers.length === 0) {
                            gainersTable.innerHTML = `
                                <tr>
                                    <td colspan="4" class="empty">No gainers data available</td>
                                </tr>
                            `;
                        } else {
                            let gainersHTML = '';
                            gainers.forEach(stock => {
                                gainersHTML += `
                                    <tr>
                                        <td>${stock.symbol}</td>
                                        <td>$${formatNumber(stock.price)}</td>
                                        <td class="up">+$${formatNumber(stock.change)}</td>
                                        <td class="up">+${formatNumber(stock.percent_change)}%</td>
                                    </tr>
                                `;
                            });
                            gainersTable.innerHTML = gainersHTML;
                        }
                        
                        // Process losers
                        const losers = data.losers || [];
                        if (losers.length === 0) {
                            losersTable.innerHTML = `
                                <tr>
                                    <td colspan="4" class="empty">No losers data available</td>
                                </tr>
                            `;
                        } else {
                            let losersHTML = '';
                            losers.forEach(stock => {
                                losersHTML += `
                                    <tr>
                                        <td>${stock.symbol}</td>
                                        <td>$${formatNumber(stock.price)}</td>
                                        <td class="down">-$${formatNumber(Math.abs(stock.change))}</td>
                                        <td class="down">-${formatNumber(Math.abs(stock.percent_change))}%</td>
                                    </tr>
                                `;
                            });
                            losersTable.innerHTML = losersHTML;
                        }
                        
                        updateTimestamp();
                        
                    } catch (error) {
                        console.error('Error fetching data:', error);
                        gainersTable.innerHTML = `
                            <tr>
                                <td colspan="4" class="error">Error fetching data. Please try again.</td>
                            </tr>
                        `;
                        losersTable.innerHTML = `
                            <tr>
                                <td colspan="4" class="error">Error fetching data. Please try again.</td>
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

# API endpoint to get market movers data
@market_movers_bp.route('/market-movers/data')
def get_market_movers_data():
    data = get_market_movers()
    return jsonify(data) 