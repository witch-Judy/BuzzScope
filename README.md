# BuzzScope - Keyword Tracking Across Tech Communities

BuzzScope is a comprehensive keyword tracking application that monitors keyword popularity across multiple tech communities including Hacker News, Reddit, Discord, and YouTube. It provides detailed analytics, trend analysis, and cross-platform insights.

## Current Status

✅ **Fully Functional** - The application is ready for use with:
- Pre-processed historical data for 4 keywords (ai, iot, mqtt, unified_namespace)
- Optimized Streamlit frontend with cached results
- Discord special display with channel distribution charts
- Cross-platform comparison and trend analysis
- All major features working and tested

## ✨ Features

### 📊 Analytics & Metrics
- **Volume Metrics**: Mention count, unique users, interaction count
- **Trend Analysis**: Time series analysis with moving averages
- **Cross-Platform Comparison**: Side-by-side keyword comparison
- **User Insights**: Top contributors and cross-platform user identification

### 🌐 Platform Support
- **Hacker News**: Stories and comments via official API
- **Reddit**: Posts and comments via PRAW
- **YouTube**: Videos via YouTube Data API v3
- **Discord**: Messages from local JSON archives

### 🎯 Key Capabilities
- Real-time data collection and analysis
- Modular, extensible architecture
- Efficient Parquet-based storage
- Beautiful Streamlit web interface
- Command-line tools for automation
- Keyword management system

## 🚀 Quick Start

### Option 1: Use Pre-processed Data (Recommended)

The application comes with pre-processed data for 4 keywords. Simply run:

```bash
streamlit run app_simple_historical.py --server.port 8501
```

Then visit http://localhost:8501 to see the analysis results.

### Option 2: Full Installation

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd BuzzScope

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the environment template and configure your API keys:

```bash
cp env.example .env
```

Edit `.env` with your API credentials:

```env
# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key_here

# Reddit API (via PRAW)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_app_name/1.0

# Optional: Discord Bot Token
DISCORD_BOT_TOKEN=your_discord_bot_token
```

### 3. Launch the Application

```bash
# Launch Streamlit web interface
python run.py app

# Or directly with Streamlit
streamlit run app.py
```

## 🛠️ Usage

### Web Interface

The Streamlit application provides an intuitive web interface with:

- **Keyword Input**: Enter keywords to track
- **Platform Selection**: Choose which platforms to monitor
- **Analysis Types**: Single keyword, comparison, or cross-platform insights
- **Data Collection**: Collect fresh data with one click
- **Visualizations**: Interactive charts and graphs

### Command Line Interface

```bash
# Collect data for a keyword
python run.py collect "UNS" --platforms hackernews reddit --days 30

# Analyze a keyword
python run.py analyze "UNS" --days 30

# Manage keywords
python run.py keywords

# Show storage statistics
python run.py stats
```

### Keyword Management

```bash
python run.py keywords
```

Interactive keyword management allows you to:
- Add/remove keywords
- Configure platforms per keyword
- Set analysis frequency
- Export/import keyword configurations

## 📁 Project Structure

```
BuzzScope/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── models.py              # Data models and schemas
│   ├── storage.py             # Parquet-based storage system
│   ├── analysis.py            # Analysis engine
│   ├── keyword_manager.py     # Keyword management
│   └── collectors/
│       ├── __init__.py
│       ├── base_collector.py  # Base collector class
│       ├── hackernews_collector.py
│       ├── reddit_collector.py
│       ├── youtube_collector.py
│       └── discord_collector.py
├── data/                      # Data storage directory
│   ├── hackernews/           # Hacker News data
│   ├── reddit/               # Reddit data
│   ├── youtube/              # YouTube data
│   ├── discord/              # Discord data
│   └── analysis/             # Analysis results
├── app.py                    # Streamlit application
├── run.py                    # Command-line interface
├── requirements.txt          # Python dependencies
├── env.template             # Environment template
└── README.md               # This file
```

## 🔧 API Setup

### YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Add the API key to your `.env` file

### Reddit API
1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Create a new app (script type)
3. Note the client ID and secret
4. Add credentials to your `.env` file

### Discord Data
1. Use [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) to export chat data
2. Place JSON files in `./data/discord_archives/`
3. The system will automatically process the archives

## 📊 Data Storage

BuzzScope uses Parquet format for efficient data storage:

- **Partitioned by platform and date**
- **Compressed with Snappy compression**
- **Schema evolution support**
- **Fast query performance**

Data is organized as:
```
data/
├── hackernews/
│   ├── hackernews_20240101.parquet
│   └── hackernews_20240102.parquet
├── reddit/
│   ├── reddit_20240101.parquet
│   └── reddit_20240102.parquet
└── ...
```

## 🔍 Analysis Features

### Volume Metrics
- Total mentions across platforms
- Unique author count
- Interaction metrics (likes, upvotes, comments, views)

### Trend Analysis
- Daily mention trends
- Moving averages
- Growth rate calculations
- Peak activity identification

### Cross-Platform Insights
- Platform comparison
- Common users across platforms
- Platform-specific behavior patterns

### Keyword Comparison
- Side-by-side keyword performance
- Relative popularity metrics
- Trend comparisons

## 🎨 Customization

### Adding New Platforms

1. Create a new collector class inheriting from `BaseCollector`
2. Implement required methods: `search_keyword()` and `get_recent_posts()`
3. Add platform configuration to `Config.PLATFORMS`
4. Update the platform registry in `models.py`

### Custom Analysis

Extend the `BuzzScopeAnalyzer` class to add custom analysis methods:

```python
def custom_analysis(self, keyword: str, **kwargs):
    # Your custom analysis logic
    pass
```

### UI Customization

The Streamlit app can be customized by modifying `app.py`:
- Add new analysis types
- Create custom visualizations
- Implement new data collection workflows

## 🚀 Advanced Usage

### Automated Data Collection

Set up a cron job for automated data collection:

```bash
# Collect data every 6 hours
0 */6 * * * cd /path/to/BuzzScope && python run.py collect "UNS" --days 7
```

### Batch Analysis

Analyze multiple keywords:

```python
from src.analysis import BuzzScopeAnalyzer

analyzer = BuzzScopeAnalyzer()
keywords = ["UNS", "IoT", "MQTT", "Arduino"]

for keyword in keywords:
    results = analyzer.analyze_keyword(keyword)
    # Process results
```

### Data Export

Export analysis results:

```python
from src.storage import BuzzScopeStorage

storage = BuzzScopeStorage()
results = storage.search_posts("UNS", days_back=30)

# Export to CSV
results['hackernews'].to_csv('hackernews_uns.csv', index=False)
```

## 🐛 Troubleshooting

### Common Issues

1. **API Rate Limits**: Reduce collection frequency or implement delays
2. **Missing Data**: Check API credentials and platform availability
3. **Storage Issues**: Ensure sufficient disk space for Parquet files
4. **Memory Issues**: Process data in smaller batches

### Logging

Enable debug logging:

```bash
python run.py --log-level DEBUG collect "UNS"
```

Logs are written to `buzzscope.log` and console output.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Hacker News API
- Reddit API (PRAW)
- YouTube Data API v3
- DiscordChatExporter
- Streamlit
- Pandas and PyArrow

## 📞 Support

For questions, issues, or contributions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section

---

**Happy keyword tracking! 🔍📊**

