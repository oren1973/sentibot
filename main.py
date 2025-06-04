# main.py
import os
import sys
import pandas as pd
from datetime import datetime, date
import logging

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
    if os.path.exists(LEARNING_LOG_CSV_PATH):
        try:
            df = pd.read_csv(LEARNING_LOG_CSV_PATH)
            if 'datetime' in df.columns:
                 df['datetime'] = pd.to_datetime(df['datetime'])
            logger.info(f"Loaded existing learning log: {LEARNING_LOG_CSV_PATH} with {len(df)} entries.")
            return df
        except Exception as e:
            logger.error(f"Error loading learning log from {LEARNING_LOG_CSV_PATH}: {e}. Starting with an empty log.", exc_info=True)
    return pd.DataFrame(columns=[
        "run_id", "symbol", "datetime", "sentiment_avg", "sentiment_std", 
        "num_total_articles", "main_source_overall",
        "decision", "previous_decision", "trade_executed", "raw_scores_details"
    ])

def save_learning_log_entry(log_df: pd.DataFrame, new_entry_data: dict):
    try:
        new_entry_df = pd.DataFrame([new_entry_data])
        if log_df.empty:
            log_df = new_entry_df
        else:
            log_df = pd.concat([log_df, new_entry_df], ignore_index=True)
        log_df.to_csv(LEARNING_LOG_CSV_PATH, index=False, encoding='utf-8-sig')
        logger.info(f"Saved new entry to learning log. Total entries: {len(log_df)}")
        return log_df
    except Exception as e:
        logger.error(f"Error saving entry to learning log {LEARNING_LOG_CSV_PATH}: {e}", exc_info=True)
        return log_df

def main(force_run: bool = False):
    run_id_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_datetime_iso = datetime.now().isoformat()
    logger.info(f"🚀 Starting Sentibot run ID: {run_id_str}")

    learning_log_df = load_learning_log()
    
    try:
        os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)
        logger.info(f"Reports will be saved to directory: {REPORTS_OUTPUT_DIR}")
    except OSError as e_dir:
        logger.error(f"Could not create reports directory '{REPORTS_OUTPUT_DIR}': {e_dir}. Using current directory.")

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
            news_headlines = fetch_all_news(symbol, max_headlines_total=MAIN_MAX_TOTAL_HEADLINES)
            if news_headlines:
                logger.info(f"Fetched {len(news_headlines)} headlines from news sources for '{symbol}'.")
                symbol_headlines_data.extend(news_headlines)
            else:
                logger.info(f"No headlines from news sources for '{symbol}'.")

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
                    symbol_headlines_data.extend(reddit_content)
                else:
                    logger.info(f"No content from Reddit for '{symbol}'.")
            else:
                logger.info("Reddit fetching is disabled.")
            
            if not symbol_headlines_data:
                logger.warning(f"No headlines or content found for '{symbol}' from any source.")
                continue

            logger.info(f"Total {len(symbol_headlines_data)} items (headlines/posts) for '{symbol}' to analyze.")
            
            current_symbol_sentiments_details = []

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
            
            sentiment_scores_list = [s['score'] for s in current_symbol_sentiments_details]
            avg_sentiment_for_symbol = sum(sentiment_scores_list) / len(sentiment_scores_list)
            sentiment_std_for_symbol = pd.Series(sentiment_scores_list).std() if len(sentiment_scores_list) > 1 else 0.0
            source_counts = pd.Series([s['source'] for s in current_symbol_sentiments_details]).value_counts()
            main_source_overall_str = source_counts.index[0] if not source_counts.empty else "N/A"

            logger.info(f"Average sentiment for '{symbol}': {avg_sentiment_for_symbol:.4f} (Std: {sentiment_std_for_symbol:.4f}, Based on {len(sentiment_scores_list)} items, Main source: {main_source_overall_str})")

            recommendation_output = make_recommendation(avg_sentiment_for_symbol)
            current_trade_decision = recommendation_output.get("decision", "ERROR_NO_DECISION")
            
            logger.info(f"Recommendation for '{symbol}': {current_trade_decision} (Score: {avg_sentiment_for_symbol:.4f})")
            
            previous_decision_for_symbol = "N/A"
            if not learning_log_df.empty and symbol in learning_log_df['symbol'].values:
                symbol_specific_log = learning_log_df[learning_log_df['symbol'] == symbol].sort_values(by='datetime', ascending=False)
                if not symbol_specific_log.empty:
                    previous_decision_for_symbol = symbol_specific_log.iloc[0]['decision']
            
            logger.info(f"Previous decision for '{symbol}': {previous_decision_for_symbol}, Current decision: {current_trade_decision}")

            trade_action_taken = False
            if current_trade_decision == "BUY" and current_trade_decision != previous_decision_for_symbol:
                logger.info(f"Decision changed for {symbol} from {previous_decision_for_symbol} to BUY. Attempting trade.")
                trade_action_taken = trade_stock(symbol=symbol, decision="buy")
            elif current_trade_decision == "SELL" and previous_decision_for_symbol == "BUY":
                logger.info(f"Decision changed for {symbol} from BUY to SELL. Attempting to close position.")
                trade_action_taken = trade_stock(symbol=symbol, decision="sell")
            elif current_trade_decision == "SELL" and previous_decision_for_symbol != "BUY":
                logger.info(f"Decision is SELL for {symbol}, but no prior BUY position or prior decision was not BUY. No short selling action taken.")
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
                "raw_scores_details": str(current_symbol_sentiments_details)
            }
            learning_log_df = save_learning_log_entry(learning_log_df, learning_log_entry)
            
            aggregated_symbol_analysis.append({
                "run_id": run_id_str, "symbol": symbol, "avg_sentiment_score": avg_sentiment_for_symbol,
                "num_analyzed_headlines": len(sentiment_scores_list), "trade_decision": current_trade_decision,
                "previous_decision_logged": previous_decision_for_symbol, "trade_attempted": trade_action_taken,
                "processing_datetime": current_datetime_iso
            })

        except Exception as e_symbol_processing:
            logger.error(f"A critical error occurred while processing symbol '{symbol}': {e_symbol_processing}", exc_info=True)

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
    
    if 'send_run_success_email' in globals() and callable(send_run_success_email):
        logger.info(f"Attempting to send summary email for run ID: {run_id_str}...")
        email_sent_successfully = send_run_success_email(
            run_id_str=run_id_str, 
            attachment_path=path_to_email_attachment
        )
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
