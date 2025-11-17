# 🚀 BuzzScope Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation Steps

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install streamlit pandas pyarrow requests python-dotenv praw google-api-python-client plotly numpy python-dateutil pytz
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.template .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

### 3. Test Installation

```bash
# Run the test script
python test_setup.py
```

### 4. Launch Application

```bash
# Option 1: Using the run script
python run.py app

# Option 2: Direct Streamlit
streamlit run app.py

# Option 3: Command line interface
python run.py --help
```

## API Setup

### YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create API credentials
5. Add to `.env`: `YOUTUBE_API_KEY=your_key_here`

### Reddit
**No API setup required!** Reddit uses a public JSON API that doesn't require authentication.
- Uses public endpoints: `https://www.reddit.com/r/{subreddit}/new.json`
- No credentials needed in `.env`
- Rate limiting is automatically handled in the code

### Discord Data
1. Use [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter)
2. Export chat data as JSON
3. Place files in `./data/discord_archives/`

## Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure APIs**: Edit `.env` with your API keys (YouTube and OpenAI required, Reddit not needed)
3. **Test setup**: `python test_setup.py`
4. **Launch app**: `python run.py app`
5. **Start tracking**: Enter a keyword like "UNS" and select platforms

## Troubleshooting

### Common Issues

**ImportError: No module named 'dotenv'**
```bash
pip install python-dotenv
```

**API Rate Limits**
- Reduce collection frequency
- Check API quotas
- Implement delays between requests

**No Data Found**
- Verify API keys are correct
- Check platform availability
- Ensure keyword exists in recent posts

### Getting Help

- Check the logs in `buzzscope.log`
- Run with debug logging: `python run.py --log-level DEBUG collect "keyword"`
- Review the README.md for detailed documentation

## Next Steps

After successful installation:

1. **Add your first keyword**: Use the web interface or `python run.py keywords`
2. **Collect data**: Click "Collect Fresh Data" or use command line
3. **Analyze results**: View charts and insights in the web interface
4. **Set up automation**: Create cron jobs for regular data collection

Happy tracking! 🔍📊

