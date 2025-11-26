import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './App.css';

function App() {
  const [marketData, setMarketData] = useState([]);
  const [sentimentData, setSentimentData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStock, setSelectedStock] = useState('AAPL');

  const API_URLS = {
    scraper: process.env.REACT_APP_SCRAPER_URL || 'http://localhost:5000',
    analyzer: process.env.REACT_APP_ANALYZER_URL || 'http://localhost:5001',
    alert: process.env.REACT_APP_ALERT_URL || 'http://localhost:5002'
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Fetch market data
      const marketResponse = await axios.get(`${API_URLS.scraper}/api/latest-data`);
      setMarketData(marketResponse.data || []);

      // Fetch sentiment summary
      const sentimentResponse = await axios.get(`${API_URLS.analyzer}/api/sentiment-summary`);
      setSentimentData(sentimentResponse.data || []);

      // Fetch recent alerts
      const alertsResponse = await axios.get(`${API_URLS.alert}/api/alerts/recent`);
      setAlerts(alertsResponse.data || []);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'HIGH': return '#ef4444';
      case 'MEDIUM': return '#f59e0b';
      case 'LOW': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getSentimentColor = (score) => {
    if (score > 0.3) return '#10b981';
    if (score < -0.3) return '#ef4444';
    return '#f59e0b';
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🚀 FinTech Monitoring System</h1>
        <p>Real-time market data, AI sentiment analysis & automated alerts</p>
        <button onClick={fetchData} className="refresh-btn">
          🔄 Refresh Data
        </button>
      </header>

      {loading && <div className="loading">Loading data...</div>}

      <div className="container">
        {/* Market Data Section */}
        <section className="card">
          <h2>📊 Market Data</h2>
          <div className="stock-grid">
            {marketData.map((stock, index) => (
              <div key={index} className="stock-card">
                <h3>{stock.symbol}</h3>
                <p className="price">${parseFloat(stock.price).toFixed(2)}</p>
                <p className={parseFloat(stock.change_percent) >= 0 ? 'positive' : 'negative'}>
                  {parseFloat(stock.change_percent) >= 0 ? '▲' : '▼'}
                  {Math.abs(parseFloat(stock.change_percent)).toFixed(2)}%
                </p>
                <p className="volume">Vol: {parseInt(stock.volume).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Sentiment Analysis Section */}
        <section className="card">
          <h2>🧠 AI Sentiment Analysis (Google Gemini)</h2>
          <div className="sentiment-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="symbol" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <Legend />
                <Bar dataKey="avg_sentiment" fill="#8884d8" name="Sentiment Score" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="sentiment-details">
            {sentimentData.map((item, index) => (
              <div key={index} className="sentiment-item">
                <span className="symbol">{item.symbol}</span>
                <span 
                  className="sentiment-score"
                  style={{ color: getSentimentColor(parseFloat(item.avg_sentiment)) }}
                >
                  {parseFloat(item.avg_sentiment).toFixed(3)}
                </span>
                <span className="article-count">
                  {item.article_count} articles
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Alerts Section */}
        <section className="card">
          <h2>🔔 Recent Alerts</h2>
          <div className="alerts-container">
            {alerts.length === 0 ? (
              <p className="no-alerts">No alerts at this time ✅</p>
            ) : (
              alerts.slice(0, 10).map((alert, index) => (
                <div key={index} className="alert-item">
                  <div 
                    className="alert-severity"
                    style={{ backgroundColor: getSeverityColor(alert.severity) }}
                  >
                    {alert.severity}
                  </div>
                  <div className="alert-content">
                    <p className="alert-message">{alert.message}</p>
                    <p className="alert-meta">
                      <span className="alert-symbol">{alert.symbol}</span>
                      <span className="alert-type">{alert.alert_type}</span>
                      <span className="alert-time">
                        {new Date(alert.timestamp).toLocaleString()}
                      </span>
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* System Status */}
        <section className="card">
          <h2>⚙️ Kubernetes System Status</h2>
          <div className="status-grid">
            <div className="status-item">
              <div className="status-indicator running"></div>
              <div>
                <h4>Scraper Service</h4>
                <p>Deployment • Auto-scaling enabled</p>
              </div>
            </div>
            <div className="status-item">
              <div className="status-indicator running"></div>
              <div>
                <h4>Analyzer Service (HPA)</h4>
                <p>Deployment • CPU-based scaling</p>
              </div>
            </div>
            <div className="status-item">
              <div className="status-indicator running"></div>
              <div>
                <h4>Alert Service</h4>
                <p>Deployment • Event-driven</p>
              </div>
            </div>
            <div className="status-item">
              <div className="status-indicator running"></div>
              <div>
                <h4>PostgreSQL</h4>
                <p>StatefulSet • Persistent Volume</p>
              </div>
            </div>
            <div className="status-item">
              <div className="status-indicator running"></div>
              <div>
                <h4>Scraper CronJob</h4>
                <p>Scheduled every 30 minutes</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      <footer className="footer">
        <p>Built with React • Flask • PostgreSQL • Kubernetes</p>
        <p>Powered by Google Gemini AI</p>
      </footer>
    </div>
  );
}

export default App;
