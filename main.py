# main.py
import os
import sys
import pandas as pd
from datetime import datetime, date
import logging # הוספת logging לייבוא אם לא קיים

# --- ייבוא מהמודולים שלנו ומההגדרות ---
from settings import (
    setup_logger, NEWS_SOURCES_CONFIG, MAIN_MAX_TOTAL_HEADLINES,
    REDDIT_ENABLED, REDDIT_SUBREDDITS, REDDIT_LIMIT_PER_SUBREDDIT, REDDIT_COMMENTS_PER_POST,
    REPORTS_OUTPUT_DIR, LEARNING_LOG_CSV_PATH
)
from smart_universe import SYMBOLS 
from news_aggregator import fetch_all_news 
from reddit_scraper import get_reddit_posts # ייבוא ה-Reddit scraper
from sentiment_analyzer import analyze_sentiment
from recommender import make_recommendation
from alpaca_trader import trade_stock # ייבוא ה-Alpaca trader

logger = setup_logger("SentibotMain")

def load_learning_log() -> pd.DataFrame:
    """טוען את הלוג המצטבר או יוצר DataFrame ריק אם הקובץ לא קיים."""
    if os.path.exists(LEARNING_LOG_CSV_PATH):
        try:
            df = pd.read_csv(LEARNING_LOG_CSV_PATH)
            # ודא שעמודת התאריך מפורסרת נכון אם תצטרך למיין או לסנן לפיה
            if 'datetime' in df.columns:
                 df['datetime'] = pd.to_datetime(df['datetime'])
            logger.info(f"Loaded existing learning log: {LEARNING_LOG_CSV_PATH} with {len(df)} entries.")
            return df
        except Exception as e:
            logger.error(f"Error loading learning log from {LEARNING_LOG_CSV_PATH}: {e}. Starting with an empty log.", exc_info=True)
    return pd.DataFrame(columns=[
        "run_id", "symbol", "datetime", "sentiment_avg", "sentiment_std", 
        "num_total_articles", "main_source_overall", # אלו עמודות חדשות ללוג המצטבר
        "decision", "previous_decision", "trade_executed", "raw_scores_details" # raw_scores_details יכול להיות JSON string
    ])

def save_learning_log_entry(log_df: pd.DataFrame, new_entry_data: dict):
    """מוסיף רשומה חדשה ל-DataFrame של הלוג ושומר אותו לקובץ CSV."""
    try:
        # new_entry_df = pd.DataFrame([new_entry_data]) # ישן
        # log_df = pd.concat([log_df, new_entry_df], ignore_index=True) # ישן

        # הדרך הנכונה יותר למנוע שגיאות על סוגי נתונים היא לוודא שהמילון תואם את העמודות
        # או ליצור DataFrame חדש מהמילון ולהשתמש ב-concat.
        # אם log_df ריק ואין לו עמודות, concat עלול להיכשל.
        # יצירת DataFrame מהרשומה החדשה עם העמודות הנכונות
        new_entry_df = pd.DataFrame([new_entry_data])
        
        # אם הלוג הקיים ריק, פשוט השתמש ברשומה החדשה
        if log_df.empty:
            log_df = new_entry_df
        else:
            # ודא שהעמודות תואמות לפני concat, או השתמש ב-append (פחות מומלץ לביצועים על DF גדולים)
            # הדרך הבטוחה היא לוודא שלשני ה-DF יש אותן עמודות או להשתמש ב-concat עם join='outer' אם יש שוני
            # כרגע נניח שהעמודות יוגדרו נכון.
            log_df = pd.concat([log_df, new_entry_df], ignore_index=True)

        log_df.to_csv(LEARNING_LOG_CSV_PATH, index=False, encoding='utf-8-sig')
        logger.info(f"Saved new entry to learning log. Total entries: {len(log_df)}")
        return log_df
    except Exception as e:
        logger.error(f"Error saving entry to learning log {LEARNING_LOG_CSV_PATH}: {e}", exc_info=True)
        return log_df # החזר את הלוג המקורי (ללא התוספת) במקרה של שגיאה בשמירה


def main(force_run: bool = False):
    run_id_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_datetime_iso = datetime.now().isoformat()
    logger.info(f"🚀 Starting Sentibot run ID: {run_id_str}")

    # טעינת הלוג המצטבר
    learning_log_df = load_learning_log()
    
    # יצירת תיקיית הדוחות אם לא קיימת
    try:
        os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)
        logger.info(f"Reports will be saved to directory: {REPORTS_OUTPUT_DIR}")
    except OSError as e_dir:
        logger.error(f"Could not create reports directory '{REPORTS_OUTPUT_DIR}': {e_dir}. Using current directory.")
        # REPORTS_OUTPUT_DIR = "." # אם נרצה לשנות את הנתיב במקרה כזה

    all_individual_headline_analysis = []
    aggregated_symbol_analysis = []

    if not SYMBOLS or not isinstance(SYMBOLS, list) or len(SYMBOLS) == 0:
        logger.critical("SYMBOLS list is not defined or empty. Exiting application.")
        return

    logger.info(f"Processing symbols: {', '.join(SYMBOLS)}")

    for symbol in SYMBOLS:
        logger.info(f"--- Processing symbol: {symbol} ---")
        symbol_headlines_data = []
        try:
            # 1. איסוף חדשות ממקורות רגילים
            news_headlines = fetch_all_news(symbol, max_headlines_total=MAIN_MAX_TOTAL_HEADLINES)
            if news_headlines:
                logger.info(f"Fetched {len(news_headlines)} headlines from news sources for '{symbol}'.")
                symbol_headlines_data.extend(news_headlines)
            else:
                logger.info(f"No headlines from news sources for '{symbol}'.")

            # 2. איסוף תוכן מ-Reddit (אם מאופשר)
            if REDDIT_ENABLED:
                logger.info(f"Fetching Reddit content for '{symbol}'...")
                reddit_content = get_reddit_posts(
                    symbol=symbol,
                    subreddits_list=REDDIT_SUBREDDITS,
                    limit_per_sub=REDDIT_LIMIT_PER_SUBREDDIT,
                    comments_limit=REDDIT_COMMENTS_PER_POST
                )
                if reddit_content:
                    logger.info(f"Fetched {len(reddit_content)} items from Reddit for '{symbol}'.")
                    symbol_headlines_data.extend(reddit_content) # הוספה לרשימה המשותפת
                else:
                    logger.info(f"No content from Reddit for '{symbol}'.")
            else:
                logger.info("Reddit fetching is disabled.")
            
            if not symbol_headlines_data:
                logger.warning(f"No headlines or content found for '{symbol}' from any source.")
                continue

            logger.info(f"Total {len(symbol_headlines_data)} items (headlines/posts) for '{symbol}' to analyze.")
            
            current_symbol_sentiments_details = [] # (sentiment_score, source_name)

            for item_text, source_name in symbol_headlines_data:
                logger.debug(f"  Analyzing: [{source_name}] '{item_text[:80]}...'")
                try:
                    sentiment_score = analyze_sentiment(text=item_text, source_name=source_name)
                    if sentiment_score is not None:
                        all_individual_headline_analysis.append({
                            "run_id": run_id_str, "symbol": symbol, "source": source_name,
                            "title_or_text": item_text, "sentiment_score": sentiment_score,
                            "analysis_timestamp": current_datetime_iso
                        })
                        current_symbol_sentiments_details.append({'score': sentiment_score, 'source': source_name})
                    else:
                        logger.warning(f"Sentiment analysis returned None for item from '{source_name}' for '{symbol}'.")
                except Exception as e_sentiment:
                    logger.error(f"Error during sentiment analysis for item from '{source_name}' for '{symbol}': '{item_text[:50]}...'. Error: {e_sentiment}", exc_info=False)

            if not current_symbol_sentiments_details:
                logger.warning(f"No sentiment scores were successfully calculated for '{symbol}'. Skipping recommendation.")
                continue
            
            # חישוב סנטימנט ממוצע משוקלל (כבר נעשה בתוך analyze_sentiment פר כותרת)
            # כאן פשוט עושים ממוצע של הציונים שהתקבלו
            sentiment_scores_list = [s['score'] for s in current_symbol_sentiments_details]
            avg_sentiment_for_symbol = sum(sentiment_scores_list) / len(sentiment_scores_list)
            
            # חישוב סטיית תקן (אופציונלי, שימושי ללוג)
            sentiment_std_for_symbol = pd.Series(sentiment_scores_list).std() if len(sentiment_scores_list) > 1 else 0.0
            
            # זיהוי מקור דומיננטי (אופציונלי, שימושי ללוג)
            # main_source_overall = pd.Series([s['source'] for s in current_symbol_sentiments_details]).mode()
            # main_source_overall_str = main_source_overall[0] if not main_source_overall.empty else "N/A"
            # גישה פשוטה יותר ל-main_source:
            source_counts = pd.Series([s['source'] for s in current_symbol_sentiments_details]).value_counts()
            main_source_overall_str = source_counts.index[0] if not source_counts.empty else "N/A"


            logger.info(f"Average sentiment for '{symbol}': {avg_sentiment_for_symbol:.4f} (Std: {sentiment_std_for_symbol:.4f}, Based on {len(sentiment_scores_list)} items, Main source: {main_source_overall_str})")

            recommendation_output = make_recommendation(avg_sentiment_for_symbol)
            current_trade_decision = recommendation_output.get("decision", "ERROR_NO_DECISION")
            
            logger.info(f"Recommendation for '{symbol}': {current_trade_decision} (Score: {avg_sentiment_for_symbol:.4f})")
            
            # --- לוגיקת מסחר ושמירת לוג מצטבר ---
            previous_decision_for_symbol = "N/A"
            if not learning_log_df.empty and symbol in learning_log_df['symbol'].values:
                # קח את ההחלטה האחרונה שנרשמה עבור הסמל הזה
                # ודא שאתה ממיין לפי זמן אם יש מספר רשומות לאותו סמל ורוצה את האחרונה *באמת*
                # כרגע, ההנחה היא שהסדר בקובץ הוא כרונולוגי או שנמצא את האחרונה לפי הופעה.
                # ליתר ביטחון, נמיין ונבחר.
                symbol_specific_log = learning_log_df[learning_log_df['symbol'] == symbol].sort_values(by='datetime', ascending=False)
                if not symbol_specific_log.empty:
                    previous_decision_for_symbol = symbol_specific_log.iloc[0]['decision']
            
            logger.info(f"Previous decision for '{symbol}': {previous_decision_for_symbol}, Current decision: {current_trade_decision}")

            trade_action_taken = False
            if current_trade_decision in ["BUY", "SELL"] and current_trade_decision != previous_decision_for_symbol:
                logger.info(f"Decision changed for {symbol} from {previous_decision_for_symbol} to {current_trade_decision}. Attempting trade.")
                trade_action_taken = trade_stock(symbol=symbol, decision=current_trade_decision.lower()) # הפונקציה מצפה ל-buy/sell
                if trade_action_taken:
                    logger.info(f"Trade action {current_trade_decision} for {symbol} was successful (order submitted).")
                else:
                    logger.error(f"Trade action {current_trade_decision} for {symbol} failed (order submission failed).")
            else:
                logger.info(f"No trade action needed for {symbol}. Decision: {current_trade_decision}, Previous: {previous_decision_for_symbol}")

            # הכנת רשומה ללוג המצטבר
            learning_log_entry = {
                "run_id": run_id_str,
                "symbol": symbol,
                "datetime": current_datetime_iso,
                "sentiment_avg": round(avg_sentiment_for_symbol, 4),
                "sentiment_std": round(sentiment_std_for_symbol, 4),
                "num_total_articles": len(sentiment_scores_list),
                "main_source_overall": main_source_overall_str,
                "decision": current_trade_decision,
                "previous_decision": previous_decision_for_symbol,
                "trade_executed": trade_action_taken, # האם פקודת המסחר *נשלחה* (לא בהכרח בוצעה)
                "raw_scores_details": str(current_symbol_sentiments_details) # שמירת פרטי הציונים כ-string (אפשר גם JSON)
            }
            learning_log_df = save_learning_log_entry(learning_log_df, learning_log_entry)
            
            # הוספה גם לסיכום היומי
            aggregated_symbol_analysis.append({
                "run_id": run_id_str, "symbol": symbol, "avg_sentiment_score": avg_sentiment_for_symbol,
                "num_analyzed_headlines": len(sentiment_scores_list), "trade_decision": current_trade_decision,
                "previous_decision_logged": previous_decision_for_symbol, "trade_attempted": trade_action_taken,
                "processing_datetime": current_datetime_iso
            })

        except Exception as e_symbol_processing:
            logger.error(f"A critical error occurred while processing symbol '{symbol}': {e_symbol_processing}", exc_info=True)

    # --- שמירת דוחות CSV יומיים ---
    if all_individual_headline_analysis:
        detailed_report_df = pd.DataFrame(all_individual_headline_analysis)
        detailed_report_filename = f"detailed_headlines_{run_id_str}.csv"
        detailed_report_filepath = os.path.join(REPORTS_OUTPUT_DIR, detailed_report_filename)
        try:
            detailed_report_df.to_csv(detailed_report_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"📄 Saved daily detailed headline report: {detailed_report_filepath}")
        except Exception as e_save_detail:
            logger.error(f"Failed to save daily detailed report to '{detailed_report_filepath}': {e_save_detail}")

    path_to_email_attachment = None
    if aggregated_symbol_analysis:
        summary_report_df = pd.DataFrame(aggregated_symbol_analysis)
        summary_report_df = summary_report_df.sort_values(by="avg_sentiment_score", ascending=False)
        summary_report_filename = f"summary_decisions_{run_id_str}.csv"
        summary_report_filepath = os.path.join(REPORTS_OUTPUT_DIR, summary_report_filename)
        path_to_email_attachment = summary_report_filepath
        try:
            summary_report_df.to_csv(summary_report_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"📊 Saved daily aggregated symbol analysis report: {summary_report_filepath}")
        except Exception as e_save_summary:
            logger.error(f"Failed to save daily summary report to '{summary_report_filepath}': {e_save_summary}")
            path_to_email_attachment = None 
    
    # --- שליחת מייל סיכום ---
    if 'send_run_success_email' in globals() and callable(send_run_success_email):
        logger.info(f"Attempting to send summary email for run ID: {run_id_str}...")
        email_body_content = f"Sentibot run {run_id_str} finished.\n"
        if path_to_email_attachment:
            email_body_content += f"Summary report '{os.path.basename(path_to_email_attachment)}' is attached."
        else:
            email_body_content += "No summary report was generated to attach."
        
        # אם רוצים להוסיף עוד פרטים לגוף המייל
        # num_trades = learning_log_df[learning_log_df['run_id'] == run_id_str]['trade_executed'].sum()
        # email_body_content += f"\nNumber of trades attempted in this run: {num_trades}"
        
        email_sent_successfully = send_run_success_email(
            run_id_str=run_id_str, # הפונקציה הזו בונה את הנושא והגוף בעצמה, אולי צריך לשנות אותה
            attachment_path=path_to_email_attachment
        )
        # או לשלוח עם הפונקציה הגנרית יותר:
        # email_sent_successfully = send_email(
        #     subject=f"Sentibot Run {run_id_str} Summary",
        #     body=email_body_content,
        #     attachment_path=path_to_email_attachment
        # )
        if email_sent_successfully:
            logger.info(f"📧 Summary email for run {run_id_str} sent/attempted successfully.")
        else:
            logger.error(f"🚨 Failed to send summary email for run {run_id_str}.")
    
    logger.info(f"🏁 Sentibot run ID {run_id_str} finished.")

if __name__ == "__main__":
    force_run_param = False
    if len(sys.argv) > 1 and sys.argv[1].lower() == "force":
        logger.info("Force run argument detected via command line.") 
        force_run_param = True
    
    main(force_run=force_run_param)
