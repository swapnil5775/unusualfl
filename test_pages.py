import requests
import time
import sys

# Wait for the server to start
print("Waiting for server to start...")
time.sleep(2)

# Base URL
base_url = "http://127.0.0.1:5000"

# Pages to test
pages = [
    {"name": "Home", "url": "/"},
    {"name": "Institution List", "url": "/institution-list"},
    {"name": "Research with ticker", "url": "/research?ticker=AAPL"},
    {"name": "Seasonality", "url": "/seasonality"},
    {"name": "Seasonality Per Ticker", "url": "/seasonality/per-ticker"},
    {"name": "Seasonality Per Ticker with ticker", "url": "/seasonality/per-ticker?ticker=AAPL"},
    {"name": "ETF Market", "url": "/seasonality/etf-market"},
    {"name": "ETF Research", "url": "/etf-research"},
    {"name": "ETF Research with ticker", "url": "/etf-research?ticker=SPY"},
    {"name": "Market Tide", "url": "/market-tide"},
    {"name": "Market Tide with period", "url": "/market-tide?period=week"},
    {"name": "Market Spike", "url": "/market-spike"},
    {"name": "Market Spike with range", "url": "/market-spike?range=day"},
    {"name": "Flow Per Strike", "url": "/flow-per-strike"},
    {"name": "Flow Per Strike with ticker", "url": "/flow-per-strike?ticker=AAPL"}
]

# Test each page
all_passed = True
results = []

for page in pages:
    try:
        response = requests.get(f"{base_url}{page['url']}", timeout=5)
        status = response.status_code
        if status == 200:
            result = "✓"
        else:
            result = "✗"
            all_passed = False
        results.append({"name": page["name"], "url": page["url"], "status": status, "result": result})
    except Exception as e:
        results.append({"name": page["name"], "url": page["url"], "status": "Error", "result": "✗"})
        all_passed = False

# Print results
print("\nTest Results:")
print("=" * 60)
print(f"{'Page Name':<30} {'URL':<25} {'Status':<10} {'Result':<5}")
print("-" * 60)

for result in results:
    print(f"{result['name']:<30} {result['url']:<25} {result['status']:<10} {result['result']:<5}")

print("=" * 60)
print(f"Summary: {sum(1 for r in results if r['result'] == '✓')} of {len(pages)} pages working correctly")

# Exit with appropriate code
if all_passed:
    print("All tests passed!")
    sys.exit(0)
else:
    print("Some pages are not working. Check the logs for details.")
    sys.exit(1) 