# main.py
import os
import sys
import pandas as pd
from datetime import datetime, date
import logging
import json # הוספתי עבור שמירת raw_scores_details כ-JSON

from settings import (
    setup_logger, NEWS_SOURCES_CONFIG, MAIN_MAX_TOTAL_HEADLINES,
    REDDIT_ENABLED, REDDIT_SUBREDDITS, REDDIT_LIMIT_PER_SUBREDDIT, REDDIT_COMMENTS_PER_POST,
    REPORTS_OUTPUT_DIR, LEARNING_LOG_CSV_PATH
)
from smart_universe import SYMBOLS 
from news_aggregator import fetch_all_news 
from reddit_scraper import get_reddit_posts
from sentiment_analyzer import analyze_sentiment
from recommender import make_recommendation
from alpaca_trader import trade_stock
from email_sender import send_run_success_email

logger = setup_logger("SentibotMain")

def load_learning_log() -> pd.DataFrame:
    # הגדר DataFrame ריק למקרה שנצטרך להחזיר אותו
    empty_log_df = pd.DataFrame(columns=[
        "run_id", "symbol", "datetime", "sentiment_avg", "sentiment_std", 
        "num_total_articles", "main_source_overall",
        "decision", "previous_decision", "trade_executed", "raw_scores_details"
    ])

    logger.info(f"Checking for existing learning log at: {LEARNING_LOG_CSV_PATH}")
    if not os.path.exists(LEARNING_LOG_CSV_PATH):
        logger.warning(f"Learning log file NOT FOUND at {LEARNING_LOG_CSV_PATH}. Will start with an empty log.")
        return empty_log_df

    try:
        logger.info(f"Attempting to read CSV: {LEARNING_LOG_CSV_PATH}")
        # נסה לקרוא את הקובץ, ואם יש עמודות עם הרבה פסיקים בטקסט, ציין escapechar
        df = pd.read_csv(LEARNING_LOG_CSV_PATH, escapechar='\\') 
        logger.info(f"Successfully read {len(df)} rows from {LEARNING_LOG_CSV_PATH}.")
        
        if df.empty:
            logger.info(f"Learning log file {LEARNING_LOG_CSV_PATH} was read but is empty. Starting with an empty log.")
            return empty_log_df
            
        if 'datetime' not in df.columns:
            logger.error(f"'datetime' column MISSING in {LEARNING_LOG_CSV_PATH}. Cannot process previous decisions. Returning empty log.")
            return empty_log_df

        # נסה להמיר את עמודת התאריך
        # שמור עותק של העמודה המקורית למקרה של בעיות דיבאגינג
        df['datetime_original_str'] = df['datetime'].astype(str) 
        
        # נסה פורמט ISO8601 תחילה, ואז תן ל-Pandas לנסות להסיק אם זה נכשל
        # שימוש ב- infer_datetime_format=True יכול לעזור אם יש ערבוב קל של פורמטים.
        # errors='coerce' יכניס NaT (Not a Time) לערכים שלא ניתנים להמרה.
        df['datetime_parsed'] = pd.to_datetime(df['datetime_original_str'], errors='coerce', infer_datetime_format=True)
        
        num_failed_parsing = df['datetime_parsed'].isnull().sum()
        if num_failed_parsing > 0:
            logger.warning(f"Could not parse {num_failed_parsing} datetime strings in 'datetime' column.")
            failed_examples = df[df['datetime_parsed'].isnull()]['datetime_original_str'].head().tolist()
            logger.warning(f"Examples of original datetime strings that failed parsing: {failed_examples}")
        
        original_len = len(df)
        df.dropna(subset=['datetime_parsed'], inplace=True) # הסר שורות עם NaT
        
        # החלף את העמודה המקורית רק אם יש ערכים תקינים אחרי ההמרה
        if not df.empty:
            df['datetime'] = df['datetime_parsed'] 
        
        df.drop(columns=['datetime_parsed', 'datetime_original_str'], inplace=True, errors='ignore')
        
        if len(df) < original_len:
            logger.warning(f"Removed {original_len - len(df)} rows with invalid datetime format from learning log after parsing attempt.")
        
        if df.empty:
            logger.warning(f"Learning log became empty after datetime parsing and cleanup. Starting with an empty log.")
            return empty_log_df
        
        logger.info(f"Successfully loaded and processed learning log with {len(df)} valid entries after datetime conversion.")
        return df
    
    except pd.errors.EmptyDataError:
        logger.warning(f"Pandas EmptyDataError: The file {LEARNING_LOG_CSV_PATH} is empty or unreadable as CSV. Starting with an empty log.")
        return empty_log_df
    except Exception as e:
        logger.error(f"CRITICAL error loading or processing learning log from {LEARNING_LOG_CSV_PATH}: {e}. Starting with an empty log.", exc_info=True)
        return empty_log_df


def save_learning_log_entry(log_df: pd.DataFrame, new_entry_data: dict):
    try:
        new_entry_df = pd.DataFrame([new_entry_data])
        if 'datetime' in new_entry_df.columns: # ודא שהעמודה קיימת לפני הניסיון להמיר
            new_entry_df['datetime'] = pd.to_datetime(new_entry_df['datetime'])

        if log_df.empty:
            log_df = new_entry_df
        else:
            # ודא שגם בלוג הקיים עמודת התאריך היא מסוג datetime לפני איחוד
            if 'datetime' in log_df.columns:
                log_df['datetime'] = pd.to_datetime(log_df['datetime'], errors='coerce') # coerce למקרה שיש עדיין ערכים ישנים בעיתיים
                log_df.dropna(subset=['datetime'], inplace=True) # הסר שורות בעייתיות אם נוצרו

            log_df = pd.concat([log_df, new_entry_df], ignore_index=True)
        
        # לפני השמירה, ודא שהעמודה 'datetime' עדיין מסוג datetime
        if 'datetime' in log_df.columns and not pd.api.types.is_datetime64_any_dtype(log_df['datetime']):
             log_df['datetime'] = pd.to_datetime(log_df['datetime'], errors='coerce')
             log_df.dropna(subset=['datetime'], inplace=True)


        # שמירה: Pandas ישמור אובייקטי datetime בפורמט ISO8601 סטנדרטי ל-CSV
        # אם כי לפעמים הוא עשוי לכלול ' ' במקום 'T' אם לא מציינים date_format.
        # כדי להבטיח פורמט עם 'T', אפשר להמיר למחרוזת לפני השמירה.
        df_to_save = log_df.copy()
        if 'datetime' in df_to_save.columns and pd.api.types.is_datetime64_any_dtype(df_to_save['datetime']):
            # הפורמט הזה מבטיח 'T' ומיקרו-שניות אם קיימות
            df_to_save['datetime'] = df_to_save['datetime'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
        
        df_to_save.to_csv(LEARNING_LOG_CSV_PATH, index=False, encoding='utf-8-sig')
        logger.info(f"Saved new entry to learning log. Total entries: {len(df_to_save)}")
        return log_df # החזר את ה-log_df המקורי עם סוגי נתונים נכונים להמשך העבודה
    except Exception as e:
        logger.error(f"Error saving entry to learning log {LEARNING_LOG_CSV_PATH}: {e}", exc_info=True)
        return log_df


def main(force_run: bool = False):
    run_id_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_datetime_iso = datetime.now().isoformat(timespec='microseconds') 
    logger.info(f"🚀 Starting Sentibot run ID: {run_id_str}")
    
    learning_log_df = load_learning_log()
    
    try:
        os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)
        logger.info(f"Reports will be saved to directory: {REPORTS_OUTPUT_DIR}")
    except OSError as e_dir:
        logger.error(f"Could not create reports directory '{REPORTS_OUTPUT_DIR}': {e_dir}. Using current directory for reports.")
        # global REPORTS_OUTPUT_DIR # אם REPORTS_OUTPUT_DIR הוא גלובלי וניתן לשינוי
        # REPORTS_OUTPUT_DIR = "." # או טיפול אחר בהתאם לצורך

    all_individual_headline_analysis = []
    aggregated_symbol_analysis = []

    if not SYMBOLS or not isinstance(SYMBOLS, list) or len(SYMBOLS) == 0:
        logger.critical("SYMBOLS list is not defined or empty in smart_universe.py. Exiting application.")
        return

    logger.info(f"Processing symbols: {', '.join(SYMBOLS)}")

    for symbol in SYMBOLS:
        logger.info(f"--- Processing symbol: {symbol} ---")
        symbol_headlines_data = [] 
        try:
            news_headlines_from_aggregator = fetch_all_news(symbol, max_headlines_total=MAIN_MAX_TOTAL_HEADLINES)
            if news_headlines_from_aggregator:
                logger.info(f"Fetched {len(news_headlines_from_aggregator)} headlines from news aggregator for '{symbol}'.")
                symbol_headlines_data.extend(news_headlines_from_aggregator)
            else:
                logger.info(f"No headlines from news aggregator for '{symbol}'.")

            if REDDIT_ENABLED:
                logger.info(f"Fetching Reddit content for '{symbol}'...")
                reddit_content = get_reddit_posts(
                    symbol=symbol,
                    subreddits_list=REDDIT_SUBREDDITS,
                    limit_per_sub=REDDIT_LIMIT_PER_SUBREDDIT,
                    comments_limit=REDDIT_COMMENTS_PER_POST
                ) 
                if reddit_content:
                    logger.info(f"Fetched {len(reddit_content)} items (posts/comments) from Reddit for '{symbol}'.")
                    symbol_headlines_data.extend(reddit_content)
                else:
                    logger.info(f"No content from Reddit for '{symbol}'.")
            else:
                logger.info("Reddit fetching is disabled in settings.")
            
            if not symbol_headlines_data:
                logger.warning(f"No headlines or content found for '{symbol}' from any source after aggregation. Skipping symbol.")
                continue

            if len(symbol_headlines_data) > MAIN_MAX_TOTAL_HEADLINES:
                logger.info(f"Capping total items for '{symbol}' from {len(symbol_headlines_data)} to {MAIN_MAX_TOTAL_HEADLINES}.")
                symbol_headlines_data = symbol_headlines_data[:MAIN_MAX_TOTAL_HEADLINES]

            logger.info(f"Total {len(symbol_headlines_data)} items (headlines/posts) for '{symbol}' to analyze.")
            
            current_symbol_sentiments_details = [] 

            for item_text, source_key_from_scraper in symbol_headlines_data:
                logger.debug(f"  Analyzing: [{source_key_from_scraper}] '{item_text[:80]}...'")
                try:
                    sentiment_score = analyze_sentiment(text=item_text, source_name=source_key_from_scraper) 
                    if sentiment_score is not None:
                        all_individual_headline_analysis.append({
                            "run_id": run_id_str, "symbol": symbol, "source": source_key_from_scraper,
                            "title_or_text": item_text, "sentiment_score": sentiment_score,
                            "analysis_timestamp": current_datetime_iso
                        })
                        current_symbol_sentiments_details.append({'score': sentiment_score, 'source': source_key_from_scraper})
                    else:
                        logger.warning(f"Sentiment analysis returned None for item from '{source_key_from_scraper}' for '{symbol}'.")
                except Exception as e_sentiment:
                    logger.error(f"Error during sentiment analysis for item from '{source_key_from_scraper}' for '{symbol}': '{item_text[:50]}...'. Error: {e_sentiment}", exc_info=False)

            if not current_symbol_sentiments_details:
                logger.warning(f"No sentiment scores were successfully calculated for '{symbol}'. Skipping recommendation for this symbol.")
                continue
            
            sentiment_scores_list = [s['score'] for s in current_symbol_sentiments_details]
            avg_sentiment_for_symbol = sum(sentiment_scores_list) / len(sentiment_scores_list) if sentiment_scores_list else 0.0
            sentiment_std_for_symbol = pd.Series(sentiment_scores_list).std() if len(sentiment_scores_list) > 1 else 0.0
            
            source_names_for_symbol = [s['source'] for s in current_symbol_sentiments_details]
            source_counts = pd.Series(source_names_for_symbol).value_counts()
            main_source_overall_str = source_counts.index[0] if not source_counts.empty else "N/A"

            logger.info(f"Average sentiment for '{symbol}': {avg_sentiment_for_symbol:.4f} (Std: {sentiment_std_for_symbol:.4f}, Based on {len(sentiment_scores_list)} items, Main source by count: {main_source_overall_str})")

            recommendation_output = make_recommendation(avg_sentiment_for_symbol)
            current_trade_decision = recommendation_output.get("decision", "ERROR_NO_DECISION").upper() 
            
            logger.info(f"Recommendation for '{symbol}': {current_trade_decision} (Based on raw average score: {avg_sentiment_for_symbol:.4f})")
            
            previous_decision_for_symbol = "N/A" # אתחול
            if not learning_log_df.empty: # ודא שהלוג אינו ריק לפני גישה
                symbol_specific_entries = learning_log_df[learning_log_df['symbol'] == symbol]
                if not symbol_specific_entries.empty:
                    # ודא שעמודת התאריך היא אכן מסוג datetime לפני המיון
                    if pd.api.types.is_datetime64_any_dtype(symbol_specific_entries['datetime']):
                        symbol_specific_log = symbol_specific_entries.sort_values(by='datetime', ascending=False)
                        if not symbol_specific_log.empty:
                            previous_decision_for_symbol = str(symbol_specific_log.iloc[0]['decision']).upper()
                    else:
                        logger.warning(f"Cannot determine previous decision for {symbol} as 'datetime' column in log is not a datetime type.")
            
            logger.info(f"Previous decision for '{symbol}' from cumulative log: {previous_decision_for_symbol}, Current decision: {current_trade_decision}")

            trade_action_taken = False
            if current_trade_decision == "BUY" and current_trade_decision != previous_decision_for_symbol:
                logger.info(f"Decision changed for {symbol} from '{previous_decision_for_symbol}' to BUY. Attempting trade.")
                trade_action_taken = trade_stock(symbol=symbol, decision="buy")
            elif current_trade_decision == "SELL" and previous_decision_for_symbol == "BUY": 
                logger.info(f"Decision changed for {symbol} from BUY to SELL. Attempting to close long position.")
                trade_action_taken = trade_stock(symbol=symbol, decision="sell")
            elif current_trade_decision == "SELL" and previous_decision_for_symbol != "BUY":
                logger.info(f"Decision is SELL for {symbol}, but no prior BUY position or prior decision was not BUY. Current policy is not to short sell. No trade action taken.")
            else: 
                logger.info(f"No trade action needed for {symbol}. Decision: {current_trade_decision}, Previous: {previous_decision_for_symbol}")

            learning_log_entry = {
                "run_id": run_id_str, "symbol": symbol, "datetime": current_datetime_iso,
                "sentiment_avg": round(avg_sentiment_for_symbol, 4),
                "sentiment_std": round(sentiment_std_for_symbol, 4),
                "num_total_articles": len(sentiment_scores_list),
                "main_source_overall": main_source_overall_str,
                "decision": current_trade_decision,
                "previous_decision": previous_decision_for_symbol,
                "trade_executed": trade_action_taken,
                "raw_scores_details": json.dumps(current_symbol_sentiments_details) 
            }
            learning_log_df = save_learning_log_entry(learning_log_df, learning_log_entry)
            
            aggregated_symbol_analysis.append({
                "run_id": run_id_str, "symbol": symbol, "avg_sentiment_score": round(avg_sentiment_for_symbol, 4),
                "num_analyzed_headlines": len(sentiment_scores_list), "trade_decision": current_trade_decision,
                "previous_decision_logged": previous_decision_for_symbol, 
                "trade_attempted": trade_action_taken, 
                "processing_datetime": current_datetime_iso
            })

        except Exception as e_symbol_processing:
            logger.error(f"A critical error occurred while processing symbol '{symbol}': {e_symbol_processing}", exc_info=True)

    # --- שמירת דוחות יומיים ---
    daily_summary_report_filepath = None
    daily_detailed_report_filepath = None 

    if all_individual_headline_analysis: 
        detailed_report_df = pd.DataFrame(all_individual_headline_analysis)
        detailed_report_filename = f"detailed_headlines_{run_id_str}.csv"
        daily_detailed_report_filepath = os.path.join(REPORTS_OUTPUT_DIR, detailed_report_filename)
        try:
            detailed_report_df.to_csv(daily_detailed_report_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"📄 Saved daily detailed headline report: {daily_detailed_report_filepath}")
        except Exception as e_save_detail:
            logger.error(f"Failed to save daily detailed report to '{daily_detailed_report_filepath}': {e_save_detail}")
            daily_detailed_report_filepath = None 

    if aggregated_symbol_analysis: 
        summary_report_df = pd.DataFrame(aggregated_symbol_analysis)
        summary_report_df = summary_report_df.sort_values(by="avg_sentiment_score", ascending=False)
        summary_report_filename = f"summary_decisions_{run_id_str}.csv"
        daily_summary_report_filepath = os.path.join(REPORTS_OUTPUT_DIR, summary_report_filename)
        try:
            summary_report_df.to_csv(daily_summary_report_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"📊 Saved daily aggregated symbol analysis report: {daily_summary_report_filepath}")
        except Exception as e_save_summary:
            logger.error(f"Failed to save daily summary report to '{daily_summary_report_filepath}': {e_save_summary}")
            daily_summary_report_filepath = None 
    
    # --- שליחת מייל עם דוחות ---
    attachments_to_send = []
    if daily_summary_report_filepath and os.path.exists(daily_summary_report_filepath):
        attachments_to_send.append(daily_summary_report_filepath)
        logger.info(f"Added daily summary report to email attachments: {daily_summary_report_filepath}")
    
    if os.path.exists(LEARNING_LOG_CSV_PATH):
        attachments_to_send.append(LEARNING_LOG_CSV_PATH)
        logger.info(f"Added cumulative learning log to email attachments: {LEARNING_LOG_CSV_PATH}")
    else:
        logger.warning(f"Cumulative log file not found at {LEARNING_LOG_CSV_PATH}, will not be attached to email.")

    if 'send_run_success_email' in globals() and callable(send_run_success_email):
        if attachments_to_send: 
            logger.info(f"Attempting to send summary email for run ID: {run_id_str} with attachments: {attachments_to_send}")
            email_sent_successfully = send_run_success_email(
                run_id_str=run_id_str, 
                attachment_paths=attachments_to_send 
            )
            if email_sent_successfully:
                logger.info(f"📧 Summary email for run {run_id_str} sent/attempted successfully.")
            else:
                logger.error(f"🚨 Failed to send summary email for run {run_id_str}.")
        else:
            logger.info(f"No reports generated or cumulative log found to attach. Skipping email for run ID: {run_id_str}.")
    
    logger.info(f"🏁 Sentibot run ID {run_id_str} finished.")

if __name__ == "__main__":
    force_run_param = False
    if len(sys.argv) > 1 and sys.argv[1].lower() == "force":
        logger.info("Force run argument detected via command line.") 
        force_run_param = True
    
    main(force_run=force_run_param)
