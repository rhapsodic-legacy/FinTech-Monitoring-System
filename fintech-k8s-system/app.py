"""
Scraper Service - Fetches market data and news from public APIs
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import requests
from flask import Flask, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
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
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
STOCK_SYMBOLS = os.getenv('STOCK_SYMBOLS', 'AAPL,GOOGL,MSFT').split(',')

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres-service'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'fintech_db'),
    'user': os.getenv('POSTGRES_USER', 'fintech_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password')
}


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


class MarketDataScraper:
    """Scrapes market data from Alpha Vantage API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch current stock quote"""
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                return {
                    'symbol': symbol,
                    'price': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': quote.get('10. change percent', '0%').rstrip('%'),
                    'volume': int(quote.get('06. volume', 0)),
                    'timestamp': datetime.now()
                }
            else:
                logger.warning(f"No data returned for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    def get_intraday_data(self, symbol: str) -> Optional[List[Dict]]:
        """Fetch intraday time series data"""
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': '5min',
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Time Series (5min)' in data:
                time_series = data['Time Series (5min)']
                results = []
                
                for timestamp, values in list(time_series.items())[:10]:  # Last 10 points
                    results.append({
                        'symbol': symbol,
                        'timestamp': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume'])
                    })
                
                return results
            return None
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None


class NewsScraper:
    """Scrapes financial news from NewsAPI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
    
    def get_company_news(self, symbol: str, company_name: str = None) -> List[Dict]:
        """Fetch news articles for a company"""
        try:
            query = company_name if company_name else symbol
            
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 5,
                'apiKey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('articles'):
                articles = []
                for article in data['articles']:
                    articles.append({
                        'symbol': symbol,
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'content': article.get('content', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'fetched_at': datetime.now()
                    })
                return articles
            return []
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []


class ScraperService:
    """Main scraper service coordinator"""
    
    def __init__(self):
        self.db = DatabaseManager(DB_CONFIG)
        self.market_scraper = MarketDataScraper(ALPHA_VANTAGE_KEY)
        self.news_scraper = NewsScraper(NEWS_API_KEY) if NEWS_API_KEY else None
        
    def initialize_database(self):
        """Initialize database tables"""
        self.db.connect()
        
        # Create market_data table
        query = """
        CREATE TABLE IF NOT EXISTS market_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            price DECIMAL(10, 2),
            change_amount DECIMAL(10, 2),
            change_percent DECIMAL(5, 2),
            volume BIGINT,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_market_symbol_time ON market_data(symbol, timestamp DESC);
        """
        self.db.execute_query(query)
        
        # Create news_articles table
        query = """
        CREATE TABLE IF NOT EXISTS news_articles (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT,
            source VARCHAR(255),
            url TEXT UNIQUE,
            published_at TIMESTAMP,
            fetched_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_news_symbol ON news_articles(symbol, published_at DESC);
        """
        self.db.execute_query(query)
        
        logger.info("Database initialized successfully")
    
    def scrape_market_data(self):
        """Scrape market data for all configured symbols"""
        logger.info(f"Starting market data scrape for symbols: {STOCK_SYMBOLS}")
        results = []
        
        for symbol in STOCK_SYMBOLS:
            symbol = symbol.strip()
            quote = self.market_scraper.get_stock_quote(symbol)
            
            if quote:
                # Save to database
                query = """
                INSERT INTO market_data (symbol, price, change_amount, change_percent, volume, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    quote['symbol'],
                    quote['price'],
                    quote['change'],
                    quote['change_percent'],
                    quote['volume'],
                    quote['timestamp']
                )
                
                self.db.execute_query(query, params)
                results.append(quote)
                logger.info(f"Saved market data for {symbol}: ${quote['price']}")
            
            # Rate limiting
            time.sleep(12)  # Alpha Vantage free tier: 5 requests/minute
        
        return results
    
    def scrape_news(self):
        """Scrape news for all configured symbols"""
        if not self.news_scraper:
            logger.warning("News API key not configured, skipping news scrape")
            return []
        
        logger.info(f"Starting news scrape for symbols: {STOCK_SYMBOLS}")
        all_articles = []
        
        company_names = {
            'AAPL': 'Apple',
            'GOOGL': 'Google',
            'MSFT': 'Microsoft',
            'TSLA': 'Tesla',
            'AMZN': 'Amazon'
        }
        
        for symbol in STOCK_SYMBOLS:
            symbol = symbol.strip()
            company = company_names.get(symbol, symbol)
            articles = self.news_scraper.get_company_news(symbol, company)
            
            for article in articles:
                # Save to database (avoiding duplicates)
                query = """
                INSERT INTO news_articles (symbol, title, description, content, source, url, published_at, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                """
                params = (
                    article['symbol'],
                    article['title'],
                    article['description'],
                    article['content'],
                    article['source'],
                    article['url'],
                    article['published_at'],
                    article['fetched_at']
                )
                
                self.db.execute_query(query, params)
            
            all_articles.extend(articles)
            logger.info(f"Saved {len(articles)} articles for {symbol}")
            time.sleep(1)  # Rate limiting
        
        return all_articles
    
    def run_full_scrape(self):
        """Run complete scraping job"""
        start_time = time.time()
        logger.info("=" * 50)
        logger.info("Starting full scrape job")
        
        market_data = self.scrape_market_data()
        news_articles = self.scrape_news()
        
        duration = time.time() - start_time
        logger.info(f"Scrape completed in {duration:.2f} seconds")
        logger.info(f"Market data points: {len(market_data)}")
        logger.info(f"News articles: {len(news_articles)}")
        logger.info("=" * 50)
        
        return {
            'market_data_count': len(market_data),
            'news_articles_count': len(news_articles),
            'duration': duration
        }


# Initialize service
scraper_service = ScraperService()


# Flask Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'scraper'}), 200


@app.route('/scrape', methods=['POST'])
def trigger_scrape():
    """Manually trigger a scrape"""
    try:
        result = scraper_service.run_full_scrape()
        return jsonify({'status': 'success', 'result': result}), 200
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/latest-data', methods=['GET'])
def get_latest_data():
    """Get latest market data"""
    query = """
    SELECT DISTINCT ON (symbol) 
        symbol, price, change_amount, change_percent, volume, timestamp
    FROM market_data
    ORDER BY symbol, timestamp DESC
    """
    
    results = scraper_service.db.execute_query(query, fetch=True)
    return jsonify(results if results else []), 200


@app.route('/api/news/<symbol>', methods=['GET'])
def get_news_by_symbol(symbol):
    """Get news for a specific symbol"""
    query = """
    SELECT title, description, source, url, published_at
    FROM news_articles
    WHERE symbol = %s
    ORDER BY published_at DESC
    LIMIT 10
    """
    
    results = scraper_service.db.execute_query(query, (symbol,), fetch=True)
    return jsonify(results if results else []), 200


if __name__ == '__main__':
    logger.info("Initializing Scraper Service...")
    scraper_service.initialize_database()
    
    # Run initial scrape
    logger.info("Running initial scrape...")
    scraper_service.run_full_scrape()
    
    # Start Flask server
    port = int(os.getenv('SCRAPER_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
