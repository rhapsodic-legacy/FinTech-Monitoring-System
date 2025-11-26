"""
Alert Service - Sends email/SMS notifications when conditions trigger
"""

import os
import logging
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
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
ALERT_EMAIL = os.getenv('ALERT_EMAIL')
ALERT_PHONE = os.getenv('ALERT_PHONE')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

PRICE_CHANGE_THRESHOLD = float(os.getenv('PRICE_CHANGE_THRESHOLD', 5.0))
SENTIMENT_THRESHOLD = float(os.getenv('SENTIMENT_THRESHOLD', -0.3))

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres-service'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'fintech_db'),
    'user': os.getenv('POSTGRES_USER', 'fintech_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password')
}

# Initialize Twilio client if credentials available
try:
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        from twilio.rest import Client
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized")
    else:
        twilio_client = None
        logger.warning("Twilio credentials not configured")
except ImportError:
    twilio_client = None
    logger.warning("Twilio library not installed")


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


class EmailNotifier:
    """Sends email notifications"""
    
    def __init__(self, recipient: str):
        self.recipient = recipient
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        # For production, use proper email service
        # This is a simplified version
    
    def send_email(self, subject: str, body: str, html: bool = False) -> bool:
        """Send an email notification"""
        try:
            # Note: In production, use proper SMTP credentials
            # For demo purposes, we'll just log the email
            logger.info("=" * 60)
            logger.info(f"EMAIL NOTIFICATION")
            logger.info(f"To: {self.recipient}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body:\n{body}")
            logger.info("=" * 60)
            
            # In production, uncomment and configure:
            # msg = MIMEMultipart('alternative')
            # msg['Subject'] = subject
            # msg['From'] = sender_email
            # msg['To'] = self.recipient
            # 
            # if html:
            #     msg.attach(MIMEText(body, 'html'))
            # else:
            #     msg.attach(MIMEText(body, 'plain'))
            # 
            # with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            #     server.starttls()
            #     server.login(sender_email, sender_password)
            #     server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False


class SMSNotifier:
    """Sends SMS notifications via Twilio"""
    
    def __init__(self, recipient: str, client):
        self.recipient = recipient
        self.client = client
    
    def send_sms(self, message: str) -> bool:
        """Send an SMS notification"""
        if not self.client:
            logger.warning("Twilio client not available, logging SMS instead")
            logger.info(f"SMS to {self.recipient}: {message}")
            return False
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=self.recipient
            )
            logger.info(f"SMS sent successfully. SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False


class AlertConditionChecker:
    """Checks conditions that should trigger alerts"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def check_price_alerts(self) -> List[Dict]:
        """Check for significant price movements"""
        query = """
        WITH latest_prices AS (
            SELECT DISTINCT ON (symbol) 
                symbol, price, change_percent, timestamp
            FROM market_data
            ORDER BY symbol, timestamp DESC
        )
        SELECT * FROM latest_prices
        WHERE ABS(change_percent) > %s
        """
        
        results = self.db.execute_query(query, (PRICE_CHANGE_THRESHOLD,), fetch=True)
        
        alerts = []
        if results:
            for row in results:
                direction = "increased" if row['change_percent'] > 0 else "decreased"
                alerts.append({
                    'type': 'PRICE_ALERT',
                    'symbol': row['symbol'],
                    'severity': 'HIGH',
                    'message': f"{row['symbol']} {direction} by {abs(float(row['change_percent'])):.2f}%",
                    'price': float(row['price']),
                    'change_percent': float(row['change_percent']),
                    'timestamp': row['timestamp']
                })
        
        return alerts
    
    def check_sentiment_alerts(self) -> List[Dict]:
        """Check for negative sentiment trends"""
        query = """
        WITH recent_sentiment AS (
            SELECT symbol, 
                   AVG(sentiment_score) as avg_sentiment,
                   COUNT(*) as article_count
            FROM sentiment_analysis
            WHERE analyzed_at > NOW() - INTERVAL '6 hours'
            GROUP BY symbol
        )
        SELECT * FROM recent_sentiment
        WHERE avg_sentiment < %s AND article_count >= 3
        """
        
        results = self.db.execute_query(query, (SENTIMENT_THRESHOLD,), fetch=True)
        
        alerts = []
        if results:
            for row in results:
                alerts.append({
                    'type': 'SENTIMENT_ALERT',
                    'symbol': row['symbol'],
                    'severity': 'MEDIUM',
                    'message': f"{row['symbol']} has negative sentiment: {float(row['avg_sentiment']):.2f} across {row['article_count']} articles",
                    'avg_sentiment': float(row['avg_sentiment']),
                    'article_count': row['article_count'],
                    'timestamp': datetime.now()
                })
        
        return alerts
    
    def check_trading_signals(self) -> List[Dict]:
        """Check for strong trading signals"""
        query = """
        WITH latest_signals AS (
            SELECT DISTINCT ON (symbol)
                symbol, signal, composite_score, reason, timestamp
            FROM trading_signals
            ORDER BY symbol, timestamp DESC
        )
        SELECT * FROM latest_signals
        WHERE signal IN ('STRONG_BUY', 'STRONG_SELL')
        AND timestamp > NOW() - INTERVAL '1 hour'
        """
        
        results = self.db.execute_query(query, fetch=True)
        
        alerts = []
        if results:
            for row in results:
                alerts.append({
                    'type': 'SIGNAL_ALERT',
                    'symbol': row['symbol'],
                    'severity': 'HIGH',
                    'message': f"{row['symbol']}: {row['signal']} signal detected (score: {float(row['composite_score']):.2f})",
                    'signal': row['signal'],
                    'composite_score': float(row['composite_score']),
                    'reason': row['reason'],
                    'timestamp': row['timestamp']
                })
        
        return alerts
    
    def check_all_conditions(self) -> List[Dict]:
        """Check all alert conditions"""
        all_alerts = []
        
        try:
            price_alerts = self.check_price_alerts()
            all_alerts.extend(price_alerts)
            logger.info(f"Found {len(price_alerts)} price alerts")
        except Exception as e:
            logger.error(f"Error checking price alerts: {e}")
        
        try:
            sentiment_alerts = self.check_sentiment_alerts()
            all_alerts.extend(sentiment_alerts)
            logger.info(f"Found {len(sentiment_alerts)} sentiment alerts")
        except Exception as e:
            logger.error(f"Error checking sentiment alerts: {e}")
        
        try:
            signal_alerts = self.check_trading_signals()
            all_alerts.extend(signal_alerts)
            logger.info(f"Found {len(signal_alerts)} signal alerts")
        except Exception as e:
            logger.error(f"Error checking signal alerts: {e}")
        
        return all_alerts


class AlertService:
    """Main alert service coordinator"""
    
    def __init__(self):
        self.db = DatabaseManager(DB_CONFIG)
        self.email_notifier = EmailNotifier(ALERT_EMAIL) if ALERT_EMAIL else None
        self.sms_notifier = SMSNotifier(ALERT_PHONE, twilio_client) if ALERT_PHONE else None
        self.condition_checker = AlertConditionChecker(self.db)
    
    def initialize_database(self):
        """Initialize database tables"""
        self.db.connect()
        
        query = """
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            details JSONB,
            triggered BOOLEAN DEFAULT TRUE,
            email_sent BOOLEAN DEFAULT FALSE,
            sms_sent BOOLEAN DEFAULT FALSE,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alerts(triggered, timestamp DESC);
        """
        
        self.db.execute_query(query)
        logger.info("Database initialized successfully")
    
    def save_alert(self, alert: Dict) -> int:
        """Save alert to database"""
        query = """
        INSERT INTO alerts (symbol, alert_type, severity, message, details, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        details = {k: v for k, v in alert.items() if k not in ['symbol', 'type', 'severity', 'message', 'timestamp']}
        
        params = (
            alert['symbol'],
            alert['type'],
            alert['severity'],
            alert['message'],
            str(details),
            alert['timestamp']
        )
        
        result = self.db.execute_query(query, params, fetch=True)
        return result[0]['id'] if result else None
    
    def send_notifications(self, alerts: List[Dict]):
        """Send notifications for alerts"""
        if not alerts:
            logger.info("No alerts to send")
            return
        
        # Group alerts by severity
        high_alerts = [a for a in alerts if a['severity'] == 'HIGH']
        medium_alerts = [a for a in alerts if a['severity'] == 'MEDIUM']
        
        # Send email summary
        if self.email_notifier:
            subject = f"FinTech Alert: {len(high_alerts)} High Priority Alerts"
            body = self._format_email_body(high_alerts, medium_alerts)
            self.email_notifier.send_email(subject, body)
        
        # Send SMS for high priority only
        if self.sms_notifier and high_alerts:
            for alert in high_alerts[:3]:  # Limit to 3 SMS
                message = f"ALERT: {alert['message']}"
                self.sms_notifier.send_sms(message[:160])  # SMS length limit
    
    def _format_email_body(self, high_alerts: List[Dict], medium_alerts: List[Dict]) -> str:
        """Format email body"""
        body = "FinTech Monitoring System - Alert Report\n"
        body += "=" * 60 + "\n\n"
        
        if high_alerts:
            body += "HIGH PRIORITY ALERTS:\n"
            body += "-" * 60 + "\n"
            for alert in high_alerts:
                body += f"• {alert['message']}\n"
                body += f"  Time: {alert['timestamp']}\n\n"
        
        if medium_alerts:
            body += "\nMEDIUM PRIORITY ALERTS:\n"
            body += "-" * 60 + "\n"
            for alert in medium_alerts:
                body += f"• {alert['message']}\n"
                body += f"  Time: {alert['timestamp']}\n\n"
        
        body += "\n" + "=" * 60 + "\n"
        body += "View full details at your dashboard\n"
        
        return body
    
    def run_alert_check(self):
        """Run full alert check and notification cycle"""
        logger.info("=" * 60)
        logger.info("Starting alert check cycle")
        
        alerts = self.condition_checker.check_all_conditions()
        
        if alerts:
            logger.info(f"Found {len(alerts)} alerts")
            
            # Save alerts to database
            for alert in alerts:
                self.save_alert(alert)
            
            # Send notifications
            self.send_notifications(alerts)
        else:
            logger.info("No alerts triggered")
        
        logger.info("Alert check cycle complete")
        logger.info("=" * 60)
        
        return alerts


# Initialize service
alert_service = AlertService()


# Flask Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'alert'}), 200


@app.route('/check-alerts', methods=['POST'])
def trigger_alert_check():
    """Manually trigger alert check"""
    try:
        alerts = alert_service.run_alert_check()
        return jsonify({
            'status': 'success',
            'alerts_found': len(alerts),
            'alerts': alerts
        }), 200
    except Exception as e:
        logger.error(f"Alert check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/alerts/recent', methods=['GET'])
def get_recent_alerts():
    """Get recent alerts"""
    query = """
    SELECT symbol, alert_type, severity, message, timestamp
    FROM alerts
    WHERE triggered = true
    ORDER BY timestamp DESC
    LIMIT 20
    """
    
    results = alert_service.db.execute_query(query, fetch=True)
    return jsonify(results if results else []), 200


@app.route('/api/alerts/<symbol>', methods=['GET'])
def get_alerts_by_symbol(symbol):
    """Get alerts for specific symbol"""
    query = """
    SELECT alert_type, severity, message, timestamp
    FROM alerts
    WHERE symbol = %s AND triggered = true
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    results = alert_service.db.execute_query(query, (symbol,), fetch=True)
    return jsonify(results if results else []), 200


if __name__ == '__main__':
    logger.info("Initializing Alert Service...")
    alert_service.initialize_database()
    
    # Start Flask server
    port = int(os.getenv('ALERT_PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
