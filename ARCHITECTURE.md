# BuzzScope Architecture

## 🏗️ System Overview

BuzzScope is designed with a dual-purpose architecture:

1. **Historical Analysis** - Volume and trend analysis using pre-collected data
2. **Event-Driven Notifications** - Real-time monitoring of hot posts for keyword mentions

## 📊 Historical Analysis Service

### Purpose
Analyze keyword mentions across platforms using historical data for volume statistics and trend analysis.

### Data Sources
- **Hacker News**: Pre-collected historical data (manual collection)
- **Discord**: Pre-collected historical data (manual collection)
- **Reddit**: Real-time search with `time=all` (top 100 posts)
- **YouTube**: Real-time search (top 100 videos)

### Usage
```bash
# Analyze a keyword using historical data
python analyze_historical.py "unified namespace" --exact-match

# Save results to file
python analyze_historical.py "ai" --output results.json --format json
```

### Features
- Exact phrase matching for precise results
- Cross-platform analysis
- Date range analysis
- Historical data integration

## 🔔 Event-Driven Notification Service

### Purpose
Monitor daily hot posts for keyword mentions and send notifications via email.

### Data Sources
- **Hacker News**: Recent hot posts (50 posts)
- **Reddit**: Recent hot posts (50 posts)
- **YouTube**: Recent hot posts (50 posts)

### Usage
```bash
# Monitor keywords once
python monitor_keywords.py "unified namespace" "ai" --once

# Continuous monitoring (every 6 hours)
python monitor_keywords.py "unified namespace" "ai" --interval 6

```

### Features
- Real-time hot post monitoring
- Email notifications with HTML formatting
- Configurable check intervals
- Exact phrase matching

## 🔧 Configuration

### Environment Variables
Copy `env.example` to `.env` and configure:

```bash
# API Keys
YOUTUBE_API_KEY=your_youtube_api_key

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_notification_email@gmail.com

```

### Data Structure
```
data/
├── discord/                 # Discord historical data
│   ├── industry40/         # 103 files
│   ├── soliscada/          # 6 files
│   └── supos/             # 9 files
├── hackernews/             # Hacker News data (empty)
├── reddit/                 # Reddit data (empty)
└── youtube/                # YouTube data (empty)
```

## 🚀 Usage Examples

### Historical Analysis
```bash
# Analyze "unified namespace" with exact matching
python analyze_historical.py "unified namespace" --exact-match

# Analyze "ai" and save detailed results
python analyze_historical.py "ai" --output ai_analysis.json --format json
```

### Event-Driven Monitoring
```bash
# Monitor multiple keywords once
python monitor_keywords.py "unified namespace" "ai" "iot" --once

# Start continuous monitoring
python monitor_keywords.py "unified namespace" --interval 4
```

## 📧 Email Notifications
```json
{
  "keyword": "unified namespace",
  "platform": "reddit",
  "post": {
    "title": "Post title",
    "content": "Post content",
    "author": "username",
    "score": 42,
    "url": "https://...",
    "timestamp": "2025-10-06T10:00:00"
  },
  "found_at": "2025-10-06T10:05:00"
}
```

### Features
- HTML formatted emails
- Keyword highlighting
- Post metadata (author, score, timestamp)
- Direct links to posts
- Batch notifications for multiple mentions

### Email Content
- Subject: "BuzzScope Alert: X keyword mentions found"
- HTML body with styled post cards
- Platform indicators
- Keyword highlighting

## 🔄 Data Flow

### Historical Analysis
1. Load pre-collected data (HN, Discord)
2. Search Reddit with `time=all` (top 100)
3. Search YouTube (top 100)
4. Apply exact matching filters
5. Generate analysis results

### Event-Driven Monitoring
1. Collect today's hot posts from all platforms
2. Check for keyword mentions
3. Send email notifications
4. Update last check time

## 🛠️ Development

### Adding New Platforms
1. Create collector in `src/collectors/`
2. Add to `HistoricalAnalysisService`
3. Add to `EventDrivenService`
4. Update configuration

### Customizing Notifications
1. Modify `_create_email_body()` in `EventDrivenService`
2. Add new notification channels

## 📈 Performance Considerations

### Historical Analysis
- Reddit/YouTube searches are rate-limited
- Historical data is cached locally
- Exact matching is CPU-intensive for large datasets

### Event-Driven Monitoring
- Hot post collection is API-intensive
- Email sending has SMTP limits
- Check intervals should be reasonable (4-6 hours)

## 🔒 Security

### API Keys
- Store in `.env` file (not committed)
- Use app passwords for email
- Rotate keys regularly

### Email
- Use app-specific passwords
- Enable 2FA on email accounts
- Monitor for unusual activity
