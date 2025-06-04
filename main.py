# main.py
import os
import sys
import pandas as pd
from datetime import datetime
import logging

from settings import setup_logger, NEWS_SOURCES_CONFIG, MAIN_MAX_TOTAL_HEADLINES
from smart_universe import SYMBOLS 
from news_aggregator import fetch_all_news 
from sentiment_analyzer import analyze_sentiment
from recommender import make_recommendation
from email_sender import send_run_success_email 

logger = setup_logger("SentibotMain")

def main(force_run: bool = False):
    run_id_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"🚀 Starting Sentibot run ID: {run_id_str}")

    all_individual_headline_analysis = []
    aggregated_symbol_analysis = []

    if not SYMBOLS or not isinstance(SYMBOLS, list) or len(SYMBOLS) == 0:
        logger.critical("SYMBOLS list is not defined, empty, or not a list. Exiting application.")
        return

    logger.info(f"Processing symbols: {', '.join(SYMBOLS)}")

    for symbol in SYMBOLS:
        logger.info(f"--- Processing symbol: {symbol} ---")
        try:
            headlines_data_from_aggregator = fetch_all_news(symbol, max_headlines_total=MAIN_MAX_TOTAL_HEADLINES)

            if not headlines_data_from_aggregator:
                logger.warning(f"No headlines found for '{symbol}' after aggregation and filtering in news_aggregator.")
                continue

            logger.info(f"Received {len(headlines_data_from_aggregator)} headlines for '{symbol}' from aggregator to analyze.")
            
            current_symbol_sentiments = []

            for title_text, source_name in headlines_data_from_aggregator:
                logger.debug(f"  Analyzing: [{source_name}] '{title_text[:80]}...'")
                try:
                    sentiment_score = analyze_sentiment(text=title_text, source_name=source_name)
                    
                    if sentiment_score is not None:
                        all_individual_headline_analysis.append({
                            "run_id": run_id_str,
                            "symbol": symbol,
                            "source": source_name,
                            "title": title_text,
                            "sentiment_score": sentiment_score,
                            "analysis_timestamp": datetime.now().isoformat()
                        })
                        current_symbol_sentiments.append(sentiment_score)
                    else:
                        logger.warning(f"Sentiment analysis returned None for title from '{source_name}' for '{symbol}'.")
                
                except Exception as e_sentiment:
                    logger.error(f"Error during sentiment analysis for title from '{source_name}' for '{symbol}': '{title_text[:50]}...'. Error: {e_sentiment}", exc_info=False)

            if not current_symbol_sentiments:
                logger.warning(f"No sentiment scores were successfully calculated for '{symbol}'. Skipping recommendation.")
                continue
            
            avg_sentiment_for_symbol = sum(current_symbol_sentiments) / len(current_symbol_sentiments)
            logger.info(f"Average sentiment score for '{symbol}': {avg_sentiment_for_symbol:.4f} (based on {len(current_symbol_sentiments)} analyzed headlines)")

            recommendation_output = make_recommendation(avg_sentiment_for_symbol)
            trade_decision = recommendation_output.get("decision", "ERROR_NO_DECISION")
            
            logger.info(f"Recommendation for '{symbol}': {trade_decision} (Score: {avg_sentiment_for_symbol:.4f})")
            
            aggregated_symbol_analysis.append({
                "run_id": run_id_str,
                "symbol": symbol,
                "avg_sentiment_score": avg_sentiment_for_symbol,
                "num_analyzed_headlines": len(current_symbol_sentiments),
                "trade_decision": trade_decision,
                "processing_datetime": datetime.now().isoformat()
            })

        except Exception as e_symbol_processing:
            logger.error(f"A critical error occurred while processing symbol '{symbol}': {e_symbol_processing}", exc_info=True)

    output_dir = "sentibot_reports"
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Reports will be saved to directory: {output_dir}")
    except OSError as e_dir:
        logger.error(f"Could not create reports directory '{output_dir}': {e_dir}. Saving to current directory.")
        output_dir = "."

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

    path_to_email_attachment = None
    if aggregated_symbol_analysis:
        summary_report_df = pd.DataFrame(aggregated_symbol_analysis)
        summary_report_df = summary_report_df.sort_values(by="avg_sentiment_score", ascending=False)
        
        summary_report_filename = f"summary_decisions_{run_id_str}.csv"
        summary_report_filepath = os.path.join(output_dir, summary_report_filename)
        path_to_email_attachment = summary_report_filepath
        try:
            summary_report_df.to_csv(summary_report_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"📊 Saved aggregated symbol analysis report: {summary_report_filepath}")
        except Exception as e_save_summary:
            logger.error(f"Failed to save summary report to '{summary_report_filepath}': {e_save_summary}")
            path_to_email_attachment = None 
    else:
        logger.info("No aggregated symbol analysis data to save. Summary report will not be generated.")

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
    else:
        logger.warning("Function 'send_run_success_email' not found or not callable. Summary email not sent.")

    logger.info(f"🏁 Sentibot run ID {run_id_str} finished.")

if __name__ == "__main__":
    force_run_param = False
    if len(sys.argv) > 1 and sys.argv[1].lower() == "force":
        # שימוש בלוגר שמוגדר ברמת המודול
        logger.info("Force run argument detected via command line.") 
        force_run_param = True
    
    main(force_run=force_run_param)
