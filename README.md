# BuzzScope

**Where technology speaks, and you feel the echo**

A comprehensive keyword tracking platform that monitors technology trends across Hacker News, Reddit, and YouTube. Analyze keyword popularity, track trends, and discover insights across multiple tech communities.

## Demo

[![BuzzScope Demo](https://img.youtube.com/vi/qJBU0PBMQyw/0.jpg)](https://www.youtube.com/watch?v=qJBU0PBMQyw)

*Click the image above to watch the full demo*

## Features

### Real-time Analysis
- **Multi-platform tracking**: Hacker News, Reddit, YouTube
- **Trend visualization**: Monthly data trends with interactive charts
- **Cross-platform insights**: Compare keyword performance across platforms
- **Top contributors**: Identify key voices in each community

### Data Sources
- **Hacker News**: 2-year historical dataset with stories and comments
- **Reddit**: All-time search across subreddits
- **YouTube**: Video metadata, views, and engagement metrics
- **Discord**: Community data (limited to accessible groups)

### Key Metrics
- Total mentions and unique authors
- Monthly trend analysis
- Interaction counts (upvotes, comments, views)
- Platform-specific insights

## Quick Start

### Prerequisites
- Python 3.8+
- API keys for Reddit and YouTube (optional for demo)

### Installation

```bash
# Clone the repository
git clone https://github.com/witch-Judy/BuzzScope.git
cd BuzzScope

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp env.example .env
# Edit .env with your API keys
```

### Run the Application

```bash
# Launch the main application
streamlit run app_new_keyword_test.py --server.port 8502
```

Visit `http://localhost:8502` to access the application.

## Usage

### Pre-loaded Keywords
The application comes with pre-analyzed data for:
- `ai` - Artificial Intelligence discussions
- `iot` - Internet of Things topics  
- `mqtt` - MQTT protocol discussions
- `unified_namespace` - Industrial automation concepts

### New Keyword Analysis
1. Enter keywords in the sidebar (comma-separated)
2. Click "Collect Missing Data" for new keywords
3. View real-time analysis and trends
4. Explore cross-platform insights

### Features Overview
- **Trend Analysis**: Monthly mention trends with raw data tables
- **Platform Comparison**: Side-by-side keyword performance
- **Top Contributors**: Most active users per platform
- **Interactive Charts**: Zoom, filter, and explore data

## Data Collection

### Hacker News
- Uses 2-year historical parquet dataset
- Analyzes stories, comments, and user interactions
- Covers 7.6M+ records from 2022-2024

### Reddit
- Searches across all subreddits
- Collects posts, comments, and metadata
- Uses Reddit's public JSON API

### YouTube
- Searches video titles and descriptions
- Collects view counts, likes, and comments
- Uses YouTube Data API v3

## Architecture

```
BuzzScope/
├── app_new_keyword_test.py     # Main Streamlit application
├── src/
│   ├── collectors/             # Data collection modules
│   ├── analyzers/              # Analysis engines
│   └── visualization/          # Chart generation
├── data/
│   ├── cache/                  # Processed data cache
│   └── Hackernews_raw/         # Hacker News historical data
└── requirements.txt            # Dependencies
```

## API Setup

### Reddit API
1. Visit [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Create a new app (script type)
3. Add credentials to `.env`:
```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_app_name/1.0
```

### YouTube API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable YouTube Data API v3
3. Create API key
4. Add to `.env`:
```env
YOUTUBE_API_KEY=your_api_key
```

### Hacker News Data
The application requires a 2-year Hacker News dataset for full functionality:

**Option 1: Download from Google**
- Search for "Hacker News 2 years dataset" on Google
- Download the parquet file to `./data/Hackernews_raw/`

**Option 2: Contact the Author**
- The author can provide the dataset upon request
- Contact via GitHub issues or email

**Option 3: Use API Only**
- The application will work with real-time API data only
- Limited to recent posts and comments

## Technical Details

### Data Processing
- **Caching**: Pre-processed metrics for fast loading
- **Charts**: Pre-generated HTML charts for instant display
- **Storage**: JSON-based cache with Parquet for large datasets
- **Performance**: Optimized for real-time analysis

### Supported Platforms
- **Hacker News**: Official API + 2-year historical dataset (7.6M+ records)
- **Reddit**: Public JSON API (no authentication required)
- **YouTube**: Data API v3 with quota management
- **Discord**: Community data (requires access to specific groups)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For questions or issues:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the documentation

---

**Start tracking technology trends today**