# FinanceHub

A modern financial dashboard web application built with Flask that provides various tools for financial analysis and research.

## Features

- **Home Dashboard**: Overview of all available features and tools.
- **Institution List**: View top financial institutions and their holdings.
- **Stock Research**: Research stocks with detailed metrics and charts.
- **Seasonality Analysis**: Analyze seasonal patterns in stock performance.
- **ETF Research**: Explore ETFs, their holdings, and sector exposure.
- **Market Tide**: Analyze the flow of money across market sectors over different time periods.
- **Market Spike**: Track market volatility and spike events with real-time data.
- **Flow Per Strike**: Analyze options flow data by strike price with detailed call and put information.

## Pages

1. **Home** (`/`): Main dashboard with links to all features.
2. **Institution List** (`/institution-list`): List of financial institutions and their holdings.
3. **Research** (`/research`): Stock research tool with ticker search.
4. **Seasonality** (`/seasonality`): Seasonality analysis tools.
5. **Seasonality Per Ticker** (`/seasonality/per-ticker`): Analyze seasonal patterns for specific stocks.
6. **ETF Market** (`/seasonality/etf-market`): Market-wide ETF seasonality analysis.
7. **ETF Research** (`/etf-research`): Research ETFs, their holdings, and sector exposure.
8. **Market Tide** (`/market-tide`): Analyze money flow across market sectors with day/week/month/year views.
9. **Market Spike** (`/market-spike`): Track market volatility and spike events with time-series data.
10. **Flow Per Strike** (`/flow-per-strike`): Analyze options flow data by strike price with detailed call and put information.

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/financehub.git
cd financehub
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Technologies Used

- Flask
- Chart.js
- Font Awesome
- yfinance
- pytz
- Modern CSS with light/dark mode support