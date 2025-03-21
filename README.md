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

## Deployment

### Render Deployment

The application is configured for automatic deployment to Render:

1. Push changes to the main branch or heroku-deployment branch
2. GitHub Actions will automatically trigger a deployment to Render
3. Monitor the deployment status in the GitHub Actions tab

### Deployment Status

The application is currently deployed and running on Render. The deployment is managed through GitHub Actions, which automatically deploys changes when pushed to the main branch.

Current deployment URL: [FinanceHub on Render](https://financehub.onrender.com) (Replace with your actual Render URL)

Last deployed: March 21, 2024

### Setting Up Automated Deployment

To set up automated deployment to Render:

1. Create a Render account and set up a Web Service for your application
2. Get your Render API key from the Render dashboard
3. Get your Service ID from your Render service URL
4. Add the following secrets to your GitHub repository:
   - `RENDER_API_KEY`: Your Render API key
   - `RENDER_SERVICE_ID`: Your Render service ID
5. Push changes to the main branch to trigger deployment

### Manual Deployment

You can also deploy manually to Render:

1. Sign up for [Render](https://render.com/)
2. Create a new Web Service and select your GitHub repository
3. Use the following settings:
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Set environment variables in the Render dashboard for any API keys or secrets
5. Click "Create Web Service" to deploy