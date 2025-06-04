# main.py (גרסה מעודכנת ותואמת)

import os
import sys
import pandas as pd
from datetime import datetime
import logging # ייבוא logging

# --- ייבוא מהמודולים שלנו ומההגדרות ---
from settings import setup_logger, NEWS_SOURCES_CONFIG # ודא ש-NEWS_SOURCES_CONFIG קיים ב-settings
# אם SYMBOLS מוגדר ב-smart_universe.py:
from smart_universe import SYMBOLS 
# אם אתה רוצה להשתמש במגבלה הכוללת שהוגדרה ב-settings:
from settings import DEFAULT_MAX_HEADLINES_PER_SOURCE # זה ישמש כמגבלה *פר מקור* ב-news_aggregator
# מגבלה *כוללת* ל-main.py אפשר להגדיר כאן או גם ב-settings
MAIN_MAX_TOTAL_HEADLINES = 50 

# ודא שהשם של הקובץ המאגד והפונקציה תואמים למה שיש לך
from news_aggregator import fetch_all_news 
from sentiment_analyzer import analyze_sentiment
from recommender import make_recommendation
# ודא ש-email_sender.py מיובא והפונקציה קיימת
from email_sender import send_run_success_email 

# אתחול הלוגר הראשי של האפליקציה
# אתה יכול לקרוא ל-setup_logger רק פעם אחת ברמת האפליקציה אם תרצה,
# או לאתחל אותו בכל מודול עם __name__ כפי שעשינו.
# כאן, ניצור לוגר ספציפי ל-main.
logger = setup_logger("SentibotMain")

def main(force_run: bool = False): # הוספתי Type Hint ל-force_run
    run_id_str = datetime.now().strftime("%Y%m%d_%H%M%S") # ID לריצה הנוכחית
    logger.info(f"🚀 Starting Sentibot run ID: {run_id_str}")

    # רשימה לאיסוף כל נתוני הכותרות וציוני הסנטימנט שלהן
    all_individual_headline_analysis = []
    # רשימה לאיסוף סיכום פר סמל (סנטימנט ממוצע והחלטה)
    aggregated_symbol_analysis = []

    if not SYMBOLS or not isinstance(SYMBOLS, list) or len(SYMBOLS) == 0:
        logger.critical("SYMBOLS list is not defined, empty, or not a list. Exiting application.")
        # כאן אפשר לשקול שליחת מייל שגיאה אם רוצים
        return

    logger.info(f"Processing symbols: {', '.join(SYMBOLS)}")

    for symbol in SYMBOLS:
        logger.info(f"--- Processing symbol: {symbol} ---")
        try:
            # קריאה לפונקציה המאגדת מה-news_aggregator
            # היא מחזירה list[tuple[str, str]] כלומר [(title1, source1), (title2, source2), ...]
            # ה-DEFAULT_MAX_HEADLINES_PER_SOURCE מ-settings ישפיע בתוך fetch_all_news
            # על כמה כותרות נלקחות מכל מקור *לפני* הסינון הסופי של כפילויות.
            # ה-MAIN_MAX_TOTAL_HEADLINES כאן ישלוט על כמה סך הכל כותרות נעבד ב-main.py.
            headlines_data_from_aggregator = fetch_all_news(symbol, max_headlines_total=MAIN_MAX_TOTAL_HEADLINES)

            if not headlines_data_from_aggregator:
                logger.warning(f"No headlines found for '{symbol}' after aggregation and filtering in news_aggregator.")
                continue

            logger.info(f"Received {len(headlines_data_from_aggregator)} headlines for '{symbol}' from aggregator to analyze.")
            
            current_symbol_sentiments = [] # רשימה לאיסוף ציוני סנטימנט עבור הסמל הנוכחי

            # הלולאה עוברת על רשימת ה-tuples שהתקבלה
            for title_text, source_name in headlines_data_from_aggregator:
                logger.debug(f"  Analyzing: [{source_name}] '{title_text[:80]}...'")
                try:
                    # העברת הטקסט ושם המקור לפונקציית ניתוח הסנטימנט
                    # הפונקציה תחזיר ציון משוקלל (או None אם יש שגיאה)
                    sentiment_score = analyze_sentiment(text=title_text, source_name=source_name)
                    
                    if sentiment_score is not None:
                        all_individual_headline_analysis.append({
                            "run_id": run_id_str,
                            "symbol": symbol,
                            "source": source_name,
                            "title": title_text,
                            "sentiment_score": sentiment_score, # שם עמודה עקבי
                            "analysis_timestamp": datetime.now().isoformat()
                        })
                        current_symbol_sentiments.append(sentiment_score)
                    else:
                        logger.warning(f"Sentiment analysis returned None for title from '{source_name}' for '{symbol}'.")
                
                except Exception as e_sentiment:
                    # לוג של השגיאה הספציפית בניתוח הסנטימנט
                    logger.error(f"Error during sentiment analysis for title from '{source_name}' for '{symbol}': '{title_text[:50]}...'. Error: {e_sentiment}", exc_info=False) # exc_info=False כדי לא להציף אם יש הרבה כאלה

            if not current_symbol_sentiments:
                logger.warning(f"No sentiment scores were successfully calculated for '{symbol}'. Skipping recommendation.")
                continue # דלג לשלב הבא של הלולאה (הסמל הבא)
            
            # חישוב סנטימנט ממוצע לסמל על בסיס הציונים המשוקללים
            avg_sentiment_for_symbol = sum(current_symbol_sentiments) / len(current_symbol_sentiments)
            logger.info(f"Average sentiment score for '{symbol}': {avg_sentiment_for_symbol:.4f} (based on {len(current_symbol_sentiments)} analyzed headlines)")

            # --- קבלת המלצה ---
            # חשוב: ודא שהספים ב-recommender.py מתאימים לסקאלה של avg_sentiment_for_symbol!
            # אם avg_sentiment_for_symbol הוא ממוצע של ציונים משוקללים (שיכולים להיות > 1),
            # אז הספים המקוריים של 0.2 ו- -0.2 לא יתאימו.
            # נניח כרגע ש-recommender.py עודכן להתמודד עם זה או שהספים הותאמו.
            recommendation_output = make_recommendation(avg_sentiment_for_symbol)
            trade_decision = recommendation_output.get("decision", "ERROR_NO_DECISION")
            
            logger.info(f"Recommendation for '{symbol}': {trade_decision} (Score: {avg_sentiment_for_symbol:.4f})")
            
            # איסוף נתונים לסיכום פר סמל
            aggregated_symbol_analysis.append({
                "run_id": run_id_str,
                "symbol": symbol,
                "avg_sentiment_score": avg_sentiment_for_symbol,
                "num_analyzed_headlines": len(current_symbol_sentiments),
                "trade_decision": trade_decision, # שם עמודה עקבי
                "processing_datetime": datetime.now().isoformat()
            })

            # --------------------------------------------------------------------
            # כאן המקום להוסיף לוגיקה של מסחר אם רוצים:
            # 1. קריאת החלטה קודמת מה-learning_log.csv ההיסטורי.
            # 2. השוואה להחלטה הנוכחית (trade_decision).
            # 3. אם יש שינוי וזה BUY או SELL -> קריאה ל-alpaca_trader.trade_stock(symbol, trade_decision).
            # 4. שמירת ההחלטה והפרטים ל-learning_log.csv המצטבר.
            # כרגע, לוגיקה זו לא כלולה כי היא לא הייתה בקוד ה-main האחרון ששיתפת.
            # --------------------------------------------------------------------

        except Exception as e_symbol_processing:
            logger.error(f"A critical error occurred while processing symbol '{symbol}': {e_symbol_processing}", exc_info=True)
            # המשך לסמל הבא גם אם אחד נכשל

    # --- שמירת דוחות CSV בסוף הריצה ---
    output_dir = "sentibot_reports" # תיקייה לשמירת הדוחות
    try:
        os.makedirs(output_dir, exist_ok=True) # צור את התיקייה אם היא לא קיימת
        logger.info(f"Reports will be saved to directory: {output_dir}")
    except OSError as e_dir:
        logger.error(f"Could not create reports directory '{output_dir}': {e_dir}. Saving to current directory.")
        output_dir = "." # שמור בתיקייה הנוכחית אם יצירת התיקייה נכשלה

    # דוח מפורט של כל כותרת וסנטימנט
    if all_individual_headline_analysis:
        detailed_report_df = pd.DataFrame(all_individual_headline_analysis)
        detailed_report_filename = f"detailed_headlines_{run_id_str}.csv"
        detailed_report_filepath = os.path.join(output_dir, detailed_report_filename)
        try:
            detailed_report_df.to_csv(detailed_report_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"📄 Saved detailed headline analysis report: {detailed_report_filepath}")
        except Exception as e_save_detail:
            logger.error(f"Failed to save detailed report to '{detailed_report_filepath}': {e_save_detail}")
    else:
        logger.warning("No individual headline data was collected in this run. Detailed report will not be generated.")

    # דוח סיכום פר סמל עם סנטימנט ממוצע והחלטה
    path_to_email_attachment = None
    if aggregated_symbol_analysis:
        summary_report_df = pd.DataFrame(aggregated_symbol_analysis)
        summary_report_df = summary_report_df.sort_values(by="avg_sentiment_score", ascending=False) # מיון לפי סנטימנט
        
        summary_report_filename = f"summary_decisions_{run_id_str}.csv"
        summary_report_filepath = os.path.join(output_dir, summary_report_filename)
        path_to_email_attachment = summary_report_filepath # שמירת הנתיב לשליחה במייל
        try:
            summary_report_df.to_csv(summary_report_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"📊 Saved aggregated symbol analysis report: {summary_report_filepath}")
        except Exception as e_save_summary:
            logger.error(f"Failed to save summary report to '{summary_report_filepath}': {e_save_summary}")
            path_to_email_attachment = None # אם השמירה נכשלה, אל תנסה לשלוח קובץ שלא קיים
    else:
        logger.info("No aggregated symbol analysis data to save. Summary report will not be generated.")

    # --- שליחת מייל סיכום ---
    # ודא שהפונקציה send_run_success_email מיובאת וקיימת
    if 'send_run_success_email' in globals() and callable(send_run_success_email):
        logger.info(f"Attempting to send summary email for run ID: {run_id_str}...")
        email_sent_successfully = send_run_success_email(
            run_id_str=run_id_str, 
            attachment_path=path_to_email_attachment # ישלח גם אם path_to_email_attachment הוא None
        )
        if email_sent_successfully:
            logger.info(f"📧 Summary email for run {run_id_str} sent/attempted successfully.")
        else:
            logger.error(f"🚨 Failed to send summary email for run {run_id_str}.")
    else:
        logger.warning("Function 'send_run_success_email' not found or not callable. Summary email not sent.")

    logger.info(f"🏁 Sentibot run ID {run_id_str} finished.")

if __name__ == "__main__":
    # --- הגדרות להרצה מקומית או דרך CLI ---
    # (אפשר להוסיף טעינת .env כאן לפיתוח מקומי)
    # from dotenv import load_dotenv
    # load_dotenv()
    
    # הגדרת רמת לוגינג גלובלית לבדיקות יכולה להיעשות כאן.
    # למשל, אם רוצים לראות הודעות DEBUG כשמריצים ידנית:
    # השורה הבאה תגדיר את הלוגר הראשי של האפליקציה לרמת DEBUG.
    # זה ישפיע רק אם הלוגרים במודולים האחרים לא דורסים את זה עם רמה גבוהה יותר (כמו INFO).
    # main_execution_logger = setup_logger("SentibotMain", level=logging.DEBUG)
    # main_execution_logger.info("Running main() with overall DEBUG level logging for SentibotMain.")
    
    # בדוק אם יש ארגומנט "force" מה-command line
    force_run_param = False
    if len(sys.argv) > 1 and sys.argv[1].lower() == "force":
        logger.info("Force run argument detected via command line.") # ישתמש בלוגר שמוגדר למעלה
        force_run_param = True
    
    main(force_run=force_run_param)
