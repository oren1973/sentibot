# Sentibot – Weighted Sentiment Engine
# Calculates a time-decayed, source-weighted sentiment score per stock symbol

import math
from datetime import datetime
from typing import List, Dict

# הגדרת מחלקה לאובייקט כותרת
class Headline:
    def __init__(self, symbol: str, sentiment_score: float, source: str, published_at: datetime):
        self.symbol = symbol
        self.sentiment_score = sentiment_score
        self.source = source
        self.published_at = published_at

# פונקציה לחישוב סנטימנט משוקלל לכל מניה
def calculate_weighted_sentiment(headlines: List[Headline], source_weights: Dict[str, float] = None, lambda_decay: float = 0.1) -> Dict[str, float]:
    if source_weights is None:
        source_weights = {
            'Bloomberg': 1.3,
            'CNBC': 1.2,
            'Yahoo Finance': 1.0,
            'Unknown': 0.8
        }

    symbol_scores = {}
    symbol_weights = {}

    for headline in headlines:
        age_hours = (datetime.now() - headline.published_at).total_seconds() / 3600.0
        decay = math.exp(-lambda_decay * age_hours)
        source_weight = source_weights.get(headline.source, 0.8)

        weighted_score = headline.sentiment_score * source_weight * decay
        weighted_weight = source_weight * decay

        if headline.symbol not in symbol_scores:
            symbol_scores[headline.symbol] = 0.0
            symbol_weights[headline.symbol] = 0.0

        symbol_scores[headline.symbol] += weighted_score
        symbol_weights[headline.symbol] += weighted_weight

    weighted_sentiments = {
        symbol: (symbol_scores[symbol] / symbol_weights[symbol]) if symbol_weights[symbol] != 0 else 0.0
        for symbol in symbol_scores
    }

    return weighted_sentiments
