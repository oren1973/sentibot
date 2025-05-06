from investors_scraper import fetch_investors_titles

symbol = 'AAPL'
titles = fetch_investors_titles(symbol)

print(f"כותרות עבור {symbol}:")
for title in titles:
    print("-", title)
