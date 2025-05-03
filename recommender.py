def generate_recommendations(sentiment_data, threshold=0.6):
    """
    מקבל רשימת כותרות עם סנטימנט, מחזיר רשימת המלצות.
    """
    recommendations = []

    for item in sentiment_data:
        score = item["sentiment_score"]
        sentiment = item["sentiment"]
        headline = item["headline"]

        if sentiment == "חיובי" and score >= threshold:
            recommendations.append(f"קנייה: {headline} (ציון {score:.2f})")
        elif sentiment == "שלילי" and score >= threshold:
            recommendations.append(f"מכירה/זהירות: {headline} (ציון {score:.2f})")

    return recommendations
