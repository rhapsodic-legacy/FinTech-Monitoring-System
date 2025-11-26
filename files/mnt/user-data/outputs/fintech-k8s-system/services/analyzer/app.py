"""
Analyzer Service - Performs sentiment analysis using Google Gemini AI
"""

import os
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PRICE_CHANGE_THRESHOLD = float(os.getenv('PRICE_CHANGE_THRESHOLD', 5.0))

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres-service'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'fintech_db'),
    'user': os.getenv('POSTGRES_USER', 'fintech_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password')
}

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
else:
    logger.warning("Gemini API key not configured")
    gemini_model = None


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.conn = None
    
    def connect(self, retries: int = 5, delay: int = 5):
        """Connect to PostgreSQL with retry logic"""
        for attempt in range(retries):
            try:
                self.conn = psycopg2.connect(**self.config)
                logger.info("Successfully connected to PostgreSQL")
                return True
            except psycopg2.OperationalError as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    logger.error("Failed to connect to database after all retries")
                    return False
        return False
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a database query"""
        if not self.conn or self.conn.closed:
            self.connect()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    result = cursor.fetchall()
                    return result
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Database query error: {e}")
            self.conn.rollback()
            return None


class GeminiAnalyzer:
    """Performs sentiment analysis using Google Gemini"""
    
    def __init__(self, model):
        self.model = model
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text using Gemini"""
        if not self.model:
            logger.warning("Gemini model not available, using fallback")
            return self._fallback_sentiment(text)
        
        try:
            prompt = f"""
            Analyze the sentiment of the following financial news text and provide a structured response.
            
            Text: "{text}"
            
            Provide your analysis in the following JSON format:
            {{
                "sentiment_score": <float between -1.0 (very negative) and 1.0 (very positive)>,
                "sentiment_label": <"positive", "negative", or "neutral">,
                "confidence": <float between 0.0 and 1.0>,
                "key_points": [<list of 2-3 key points from the text>],
                "market_impact": <"bullish", "bearish", or "neutral">,
                "summary": <one sentence summary>
            }}
            
            Only respond with valid JSON, no other text.
            """
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up markdown code blocks if present
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            result = json.loads(result_text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return self._fallback_sentiment(text)
    
    def _fallback_sentiment(self, text: str) -> Dict:
        """Simple fallback sentiment analysis"""
        text_lower = text.lower()
        
        positive_words = ['gain', 'profit', 'up', 'increase', 'growth', 'surge', 'rally', 'bullish', 'positive']
        negative_words = ['loss', 'decline', 'down', 'decrease', 'fall', 'drop', 'bearish', 'negative']
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            score = 0.0
            label = "neutral"
        else:
            score = (pos_count - neg_count) / total
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"
        
        return {
            "sentiment_score": score,
            "sentiment_label": label,
            "confidence": 0.5,
            "key_points": ["Fallback analysis used"],
            "market_impact": "neutral",
            "summary": "Basic sentiment analysis performed"
        }
    
    def analyze_batch(self, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment for multiple articles"""
        results = []
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            sentiment = self.analyze_sentiment(text)
            
            result = {
                'article_id': article.get('id'),
                'symbol': article.get('symbol'),
                'sentiment_score': sentiment['sentiment_score'],
                'sentiment_label': sentiment['sentiment_label'],
                'confidence': sentiment['confidence'],
                'key_points': sentiment['key_points'],
                'market_impact': sentiment['market_impact'],
                'summary': sentiment['summary'],
                'analyzed_at': datetime.now()
            }
            
            results.append(result)
            time.sleep(0.5)  # Rate limiting
        
        return results


class SignalAggregator:
    """Aggregates market signals from multiple sources"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def calculate_price_signals(self, symbol: str) -> Dict:
        """Calculate price-based trading signals"""
        query = """
        SELECT price, change_percent, volume, timestamp
        FROM market_data
        WHERE symbol = %s
        ORDER BY timestamp DESC
        LIMIT 20
        """
        
        data = self.db.execute_query(query, (symbol,), fetch=True)
        
        if not data or len(data) < 2:
            return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
        
        latest = data[0]
        previous = data[1]
        
        price_change = float(latest['change_percent'])
        volume_change = (latest['volume'] - previous['volume']) / previous['volume'] * 100 if previous['volume'] > 0 else 0
        
        # Simple signal logic
        if abs(price_change) > PRICE_CHANGE_THRESHOLD:
            if price_change > 0:
                signal = 'BUY'
                reason = f'Strong upward movement: +{price_change:.2f}%'
            else:
                signal = 'SELL'
                reason = f'Strong downward movement: {price_change:.2f}%'
            strength = min(abs(price_change) / 10, 1.0)
        else:
            signal = 'HOLD'
            reason = f'Price stable at {price_change:+.2f}%'
            strength = 0.3
        
        return {
            'signal': signal,
            'strength': strength,
            'reason': reason,
            'price_change': price_change,
            'volume_change': volume_change,
            'current_price': float(latest['price'])
        }
    
    def aggregate_sentiment_signals(self, symbol: str, lookback_hours: int = 24) -> Dict:
        """Aggregate sentiment signals from news"""
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        
        query = """
        SELECT AVG(sentiment_score) as avg_sentiment,
               COUNT(*) as article_count,
               AVG(confidence) as avg_confidence
        FROM sentiment_analysis sa
        JOIN news_articles na ON sa.article_id = na.id
        WHERE na.symbol = %s AND sa.analyzed_at > %s
        """
        
        result = self.db.execute_query(query, (symbol, cutoff), fetch=True)
        
        if not result or result[0]['article_count'] == 0:
            return {
                'avg_sentiment': 0.0,
                'article_count': 0,
                'signal': 'NEUTRAL',
                'confidence': 0.0
            }
        
        data = result[0]
        avg_sentiment = float(data['avg_sentiment'] or 0)
        
        if avg_sentiment > 0.3:
            signal = 'BULLISH'
        elif avg_sentiment < -0.3:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'
        
        return {
            'avg_sentiment': avg_sentiment,
            'article_count': data['article_count'],
            'signal': signal,
            'confidence': float(data['avg_confidence'] or 0)
        }
    
    def generate_composite_signal(self, symbol: str) -> Dict:
        """Generate composite signal from all sources"""
        price_signal = self.calculate_price_signals(symbol)
        sentiment_signal = self.aggregate_sentiment_signals(symbol)
        
        # Weight the signals
        price_weight = 0.6
        sentiment_weight = 0.4
        
        # Convert signals to numeric scores
        signal_map = {'BUY': 1, 'BULLISH': 1, 'SELL': -1, 'BEARISH': -1, 'HOLD': 0, 'NEUTRAL': 0}
        
        price_score = signal_map.get(price_signal['signal'], 0) * price_signal['strength']
        sentiment_score = signal_map.get(sentiment_signal['signal'], 0) * sentiment_signal['confidence']
        
        composite_score = (price_score * price_weight) + (sentiment_score * sentiment_weight)
        
        # Determine final signal
        if composite_score > 0.3:
            final_signal = 'STRONG_BUY'
        elif composite_score > 0:
            final_signal = 'BUY'
        elif composite_score < -0.3:
            final_signal = 'STRONG_SELL'
        elif composite_score < 0:
            final_signal = 'SELL'
        else:
            final_signal = 'HOLD'
        
        return {
            'symbol': symbol,
            'final_signal': final_signal,
            'composite_score': composite_score,
            'price_signal': price_signal,
            'sentiment_signal': sentiment_signal,
            'timestamp': datetime.now()
        }


class AnalyzerService:
    """Main analyzer service coordinator"""
    
    def __init__(self):
        self.db = DatabaseManager(DB_CONFIG)
        self.gemini = GeminiAnalyzer(gemini_model)
        self.aggregator = SignalAggregator(self.db)
    
    def initialize_database(self):
        """Initialize database tables"""
        self.db.connect()
        
        query = """
        CREATE TABLE IF NOT EXISTS sentiment_analysis (
            id SERIAL PRIMARY KEY,
            article_id INTEGER REFERENCES news_articles(id),
            symbol VARCHAR(10) NOT NULL,
            sentiment_score DECIMAL(5, 4),
            sentiment_label VARCHAR(20),
            confidence DECIMAL(5, 4),
            key_points TEXT[],
            market_impact VARCHAR(20),
            summary TEXT,
            analyzed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_sentiment_symbol ON sentiment_analysis(symbol, analyzed_at DESC);
        
        CREATE TABLE IF NOT EXISTS trading_signals (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            signal VARCHAR(20) NOT NULL,
            composite_score DECIMAL(5, 4),
            price_change DECIMAL(5, 2),
            sentiment_score DECIMAL(5, 4),
            confidence DECIMAL(5, 4),
            reason TEXT,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_signals_symbol ON trading_signals(symbol, timestamp DESC);
        """
        
        self.db.execute_query(query)
        logger.info("Database initialized successfully")
    
    def analyze_recent_news(self, hours: int = 24) -> List[Dict]:
        """Analyze sentiment of recent news articles"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Get unanalyzed articles
        query = """
        SELECT na.id, na.symbol, na.title, na.description, na.content
        FROM news_articles na
        LEFT JOIN sentiment_analysis sa ON na.id = sa.article_id
        WHERE na.fetched_at > %s AND sa.id IS NULL
        ORDER BY na.fetched_at DESC
        LIMIT 20
        """
        
        articles = self.db.execute_query(query, (cutoff,), fetch=True)
        
        if not articles:
            logger.info("No new articles to analyze")
            return []
        
        logger.info(f"Analyzing {len(articles)} articles...")
        results = self.gemini.analyze_batch(articles)
        
        # Save results to database
        for result in results:
            query = """
            INSERT INTO sentiment_analysis 
            (article_id, symbol, sentiment_score, sentiment_label, confidence, 
             key_points, market_impact, summary, analyzed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                result['article_id'],
                result['symbol'],
                result['sentiment_score'],
                result['sentiment_label'],
                result['confidence'],
                result['key_points'],
                result['market_impact'],
                result['summary'],
                result['analyzed_at']
            )
            
            self.db.execute_query(query, params)
        
        logger.info(f"Saved {len(results)} sentiment analyses")
        return results
    
    def generate_signals(self, symbols: List[str]) -> List[Dict]:
        """Generate trading signals for symbols"""
        signals = []
        
        for symbol in symbols:
            try:
                signal = self.aggregator.generate_composite_signal(symbol)
                
                # Save to database
                query = """
                INSERT INTO trading_signals 
                (symbol, signal, composite_score, price_change, sentiment_score, confidence, reason, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                params = (
                    signal['symbol'],
                    signal['final_signal'],
                    signal['composite_score'],
                    signal['price_signal']['price_change'],
                    signal['sentiment_signal']['avg_sentiment'],
                    signal['sentiment_signal']['confidence'],
                    signal['price_signal']['reason'],
                    signal['timestamp']
                )
                
                self.db.execute_query(query, params)
                signals.append(signal)
                
                logger.info(f"{symbol}: {signal['final_signal']} (score: {signal['composite_score']:.2f})")
                
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
        
        return signals


# Initialize service
analyzer_service = AnalyzerService()


# Flask Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'analyzer'}), 200


@app.route('/analyze', methods=['POST'])
def trigger_analysis():
    """Manually trigger analysis"""
    try:
        symbols = os.getenv('STOCK_SYMBOLS', 'AAPL,GOOGL,MSFT').split(',')
        
        sentiment_results = analyzer_service.analyze_recent_news(hours=24)
        signal_results = analyzer_service.generate_signals([s.strip() for s in symbols])
        
        return jsonify({
            'status': 'success',
            'sentiment_analyses': len(sentiment_results),
            'trading_signals': len(signal_results),
            'signals': signal_results
        }), 200
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/sentiment-summary', methods=['GET'])
def get_sentiment_summary():
    """Get sentiment summary for all symbols"""
    query = """
    SELECT symbol, 
           AVG(sentiment_score) as avg_sentiment,
           COUNT(*) as article_count,
           AVG(confidence) as avg_confidence
    FROM sentiment_analysis
    WHERE analyzed_at > NOW() - INTERVAL '24 hours'
    GROUP BY symbol
    ORDER BY symbol
    """
    
    results = analyzer_service.db.execute_query(query, fetch=True)
    return jsonify(results if results else []), 200


@app.route('/api/signals/<symbol>', methods=['GET'])
def get_signals(symbol):
    """Get trading signals for a symbol"""
    query = """
    SELECT signal, composite_score, price_change, sentiment_score, 
           confidence, reason, timestamp
    FROM trading_signals
    WHERE symbol = %s
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    results = analyzer_service.db.execute_query(query, (symbol,), fetch=True)
    return jsonify(results if results else []), 200


if __name__ == '__main__':
    logger.info("Initializing Analyzer Service...")
    analyzer_service.initialize_database()
    
    # Start Flask server
    port = int(os.getenv('ANALYZER_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
