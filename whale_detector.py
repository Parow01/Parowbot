"""
Whale Detection Module
Contains logic for detecting whale transactions based on configurable thresholds.
"""

import logging
from typing import List, Dict, Set
import time


class WhaleDetector:
    """Detects whale transactions based on configurable thresholds."""
    
    def __init__(self, config):
        """Initialize the whale detector."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Track recently alerted trades to avoid duplicates
        self.recent_alerts: Dict[str, Set[str]] = {}
        self.alert_history_duration = 300  # 5 minutes
        
    def detect_whales(self, trades: List[Dict], symbol: str) -> List[Dict]:
        """Detect whale transactions from a list of trades."""
        if not trades:
            return []
        
        whale_trades = []
        threshold = self.config.get_whale_threshold(symbol)
        
        self.logger.debug(f"Checking {len(trades)} trades for {symbol} with threshold ${threshold:,}")
        
        for trade in trades:
            if self._is_whale_trade(trade, symbol, threshold):
                # Check if we've already alerted for this trade
                if not self._is_duplicate_alert(trade, symbol):
                    whale_trades.append(trade)
                    self._record_alert(trade, symbol)
                    self.logger.info(f"Whale detected: {symbol} - ${trade.get('qty', 0) * trade.get('price', 0):,.2f}")
        
        # Clean up old alert records
        self._cleanup_old_alerts()
        
        return whale_trades
    
    def _is_whale_trade(self, trade: Dict, symbol: str, threshold: float) -> bool:
        """Check if a trade qualifies as a whale transaction."""
        try:
            qty = float(trade.get('qty', 0))
            price = float(trade.get('price', 0))
            
            if qty <= 0 or price <= 0:
                return False
            
            # Calculate USD value of the trade
            usd_value = qty * price
            
            # Check if it meets the whale threshold
            is_whale = usd_value >= threshold
            
            if is_whale:
                self.logger.debug(f"Whale trade detected: {symbol} ${usd_value:,.2f} >= ${threshold:,.2f}")
            
            return is_whale
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error evaluating trade for whale status: {e}")
            return False
    
    def _is_duplicate_alert(self, trade: Dict, symbol: str) -> bool:
        """Check if we've already sent an alert for this trade recently."""
        try:
            # Create a unique identifier for this trade
            trade_id = trade.get('trade_id', '')
            price = trade.get('price', 0)
            qty = trade.get('qty', 0)
            timestamp = trade.get('time', 0)
            
            # Create composite ID if trade_id is not available
            if not trade_id:
                trade_id = f"{symbol}_{price}_{qty}_{timestamp}"
            
            # Check if this trade ID has been alerted recently
            if symbol in self.recent_alerts:
                if trade_id in self.recent_alerts[symbol]:
                    self.logger.debug(f"Duplicate alert avoided for {trade_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking duplicate alert: {e}")
            return False
    
    def _record_alert(self, trade: Dict, symbol: str):
        """Record that we've sent an alert for this trade."""
        try:
            # Create trade identifier
            trade_id = trade.get('trade_id', '')
            if not trade_id:
                price = trade.get('price', 0)
                qty = trade.get('qty', 0)
                timestamp = trade.get('time', 0)
                trade_id = f"{symbol}_{price}_{qty}_{timestamp}"
            
            # Initialize symbol tracking if needed
            if symbol not in self.recent_alerts:
                self.recent_alerts[symbol] = set()
            
            # Add the trade ID with timestamp
            self.recent_alerts[symbol].add(trade_id)
            
            self.logger.debug(f"Recorded alert for {trade_id}")
            
        except Exception as e:
            self.logger.warning(f"Error recording alert: {e}")
    
    def _cleanup_old_alerts(self):
        """Remove old alert records to prevent memory buildup."""
        try:
            current_time = time.time()
            
            # Simple cleanup: limit the number of tracked alerts per symbol
            max_alerts_per_symbol = 100
            
            for symbol in list(self.recent_alerts.keys()):
                if len(self.recent_alerts[symbol]) > max_alerts_per_symbol:
                    # Remove oldest half of the alerts
                    alerts_list = list(self.recent_alerts[symbol])
                    keep_count = max_alerts_per_symbol // 2
                    self.recent_alerts[symbol] = set(alerts_list[-keep_count:])
                    
                    self.logger.debug(f"Cleaned up old alerts for {symbol}")
            
        except Exception as e:
            self.logger.warning(f"Error cleaning up old alerts: {e}")
    
    def get_whale_summary(self, symbol: str) -> Dict:
        """Get a summary of whale detection for a symbol."""
        try:
            threshold = self.config.get_whale_threshold(symbol)
            recent_count = len(self.recent_alerts.get(symbol, set()))
            
            return {
                'symbol': symbol,
                'threshold_usd': threshold,
                'recent_alerts_count': recent_count,
                'detector_status': 'active'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting whale summary for {symbol}: {e}")
            return {
                'symbol': symbol,
                'threshold_usd': 0,
                'recent_alerts_count': 0,
                'detector_status': 'error'
            }
    
    def update_threshold(self, symbol: str, new_threshold: float) -> bool:
        """Update the whale threshold for a specific symbol."""
        try:
            base_symbol = symbol.replace('USDT', '').replace('USDC', '')
            self.config.WHALE_THRESHOLDS[base_symbol] = new_threshold
            
            self.logger.info(f"Updated whale threshold for {symbol} to ${new_threshold:,}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating threshold for {symbol}: {e}")
            return False
    
    def get_all_thresholds(self) -> Dict[str, float]:
        """Get all configured whale thresholds."""
        return dict(self.config.WHALE_THRESHOLDS)
