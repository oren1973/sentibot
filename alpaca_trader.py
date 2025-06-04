# alpaca_trader.py
import os
from alpaca_trade_api.rest import REST # שימוש בספרייה הישנה יותר, כפי שהיה לך
from settings import setup_logger, ALPACA_BASE_URL, TRADE_QUANTITY

logger = setup_logger(__name__)

def trade_stock(symbol: str, decision: str, quantity: int = TRADE_QUANTITY) -> bool:
    """
    שולח פקודת קנייה או מכירה ל-Alpaca.
    מחזיר True אם הפקודה נשלחה בהצלחה (לא בהכרח בוצעה), False אחרת.
    """
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        logger.error(f"Alpaca API credentials (ALPACA_API_KEY, ALPACA_SECRET_KEY) are not set. Cannot trade {symbol}.")
        return False

    logger.info(f"Attempting to trade {symbol}. Decision: {decision.upper()}, Quantity: {quantity}, URL: {ALPACA_BASE_URL}")

    try:
        api = REST(key_id=api_key, secret_key=secret_key, base_url=ALPACA_BASE_URL, api_version='v2')
        
        # בדיקת חשבון (אופציונלי, טוב לוודא שהמפתחות תקינים)
        account = api.get_account()
        logger.info(f"Alpaca account status: {account.status}, Portfolio value: {account.portfolio_value}")
        if account.trading_blocked or account.account_blocked:
            logger.error(f"Account is blocked or trading is blocked for {symbol}. Cannot submit order.")
            return False

        decision_lower = decision.lower()
        if decision_lower == "buy":
            logger.info(f"Submitting MARKET BUY order for {quantity} of {symbol}...")
            order = api.submit_order(
                symbol=symbol,
                qty=quantity,
                side="buy",
                type="market",
                time_in_force="day" # Good Till Day
            )
            logger.info(f"BUY order submitted for {symbol}. Order ID: {order.id}, Status: {order.status}")
            return True
        elif decision_lower == "sell":
            logger.info(f"Submitting MARKET SELL order for {quantity} of {symbol}...")
            # כאן צריך להחליט אם זה מכירת פוזיציה קיימת או כניסה לשורט.
            # כרגע, זו פקודת מכירה פשוטה. אם אין פוזיציה, זה עלול להיכשל או לפתוח שורט (תלוי בהגדרות החשבון).
            # לבטיחות, כדאי לבדוק אם קיימת פוזיציה לפני שליחת פקודת מכירה, אלא אם הכוונה היא לשורט.
            # position = api.get_position(symbol)
            # if position.qty > 0:
            order = api.submit_order(
                symbol=symbol,
                qty=quantity, # אם מוכרים פוזיציה קיימת, הכמות צריכה להיות תואמת
                side="sell",
                type="market",
                time_in_force="day"
            )
            logger.info(f"SELL order submitted for {symbol}. Order ID: {order.id}, Status: {order.status}")
            return True
            # else:
            #     logger.info(f"No existing position to sell for {symbol}. No SELL order placed.")
            #     return False # או True אם לא רוצים שזה ייחשב כשגיאה
        else:
            logger.warning(f"Unknown trade decision '{decision}' for {symbol}. No order placed.")
            return False

    except Exception as e:
        logger.error(f"Error submitting trade order for {symbol} (Decision: {decision}): {e}", exc_info=True)
        return False
