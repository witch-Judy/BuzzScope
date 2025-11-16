# Hot Post Monitoring System

## Overview

The Hot Post Monitoring System automatically detects trending posts across Hacker News, Reddit, and YouTube based on your specified keywords, and sends email notifications when posts become "hot" (high engagement, comments, or views).

## Features

- **Real-time Monitoring**: Continuously monitors platforms for new posts
- **Smart Heat Detection**: Uses advanced algorithms to detect trending content
- **Email Notifications**: Sends beautiful HTML emails with post details
- **Configurable Thresholds**: Customizable criteria for what constitutes a "hot" post
- **Multiple Keywords**: Monitor multiple keywords simultaneously
- **Historical Tracking**: Keeps track of previously detected hot posts

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Email Settings

Add these variables to your `.env` file:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
TO_EMAIL=your_notification_email@gmail.com
```

**For Gmail users:**
1. Enable 2-factor authentication
2. Generate an "App Password" for this application
3. Use the app password (not your regular password)

### 3. Configure API Keys

Make sure you have the required API keys in your `.env` file:

```env
# Reddit API (optional - uses public API if not provided)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_app_name/1.0

# YouTube API
YOUTUBE_API_KEY=your_youtube_api_key
```

## Usage

### Command Line Interface

#### Run Once (Test)
```bash
python monitor_hot_posts.py once
```

#### Run Continuously
```bash
python monitor_hot_posts.py continuous --interval 30
```

#### Test Email Functionality
```bash
python monitor_hot_posts.py test-email
```

#### Custom Keywords
```bash
python monitor_hot_posts.py continuous --keywords ai blockchain machine-learning --interval 15
```

### Programmatic Usage

```python
from src.services.hot_post_monitor import HotPostMonitor
from src.services.monitoring_scheduler import MonitoringScheduler

# Configuration
keywords = ['ai', 'iot', 'mqtt', 'unified_namespace']
email_config = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'your_email@gmail.com',
    'password': 'your_app_password',
    'from_email': 'your_email@gmail.com',
    'to_email': 'notifications@yourdomain.com'
}

# Run once
monitor = HotPostMonitor(keywords, email_config)
monitor.run_monitoring_cycle()

# Run continuously
scheduler = MonitoringScheduler(keywords, email_config)
scheduler.start_monitoring(interval_minutes=30)
```

## Hot Post Criteria

### Hacker News
- **Heat Score > 150** OR
- **Score > 100** OR  
- **Comments > 50**

### Reddit
- **Heat Score > 1000** OR
- **Score > 500** OR
- **Comments > 100**

### YouTube
- **Heat Score > 2000** OR
- **Views > 10,000** OR
- **Likes > 1,000** OR
- **Comments > 50**

## Heat Score Calculation

The heat score combines multiple factors:

```
Heat Score = (Base Score + Comments × Weight) × Time Factor
```

Where:
- **Base Score**: Platform-specific score (upvotes, views, etc.)
- **Comments Weight**: 2x for HN, 1.5x for Reddit, 2x for YouTube
- **Time Factor**: Newer posts get higher scores (decays over 24 hours)

## Email Notifications

### HTML Email Features
- **Beautiful Design**: Professional HTML layout
- **Post Details**: Title, URL, metrics, author, timestamp
- **Heat Score**: Visual indicator of post popularity
- **Platform Badges**: Clear platform identification
- **Keyword Tags**: Shows which keyword triggered the alert

### Email Content
Each email includes:
- Number of hot posts detected
- Post title (clickable link)
- Platform and metrics
- Heat score
- Author and timestamp
- Keyword that triggered the alert

## Monitoring Schedule

### Recommended Intervals
- **High Activity**: 15-30 minutes
- **Normal Activity**: 30-60 minutes  
- **Low Activity**: 60-120 minutes

### Best Practices
- Start with 30-minute intervals
- Monitor during peak hours (9 AM - 9 PM)
- Adjust based on notification frequency
- Use longer intervals for less active keywords

## Data Storage

### Files Created
- `data/monitoring/last_check.json` - Last monitoring timestamp
- `data/monitoring/hot_posts.json` - Historical hot posts

### Data Structure
```json
{
  "platform": "hackernews",
  "title": "Post Title",
  "url": "https://example.com",
  "author": "username",
  "score": 150,
  "comments": 75,
  "timestamp": "2024-01-01T12:00:00",
  "keyword": "ai",
  "heat_score": 250.5
}
```

## Troubleshooting

### Common Issues

#### Email Not Sending
1. Check SMTP credentials
2. Verify app password for Gmail
3. Check firewall/network settings
4. Test with `test-email` command

#### No Hot Posts Detected
1. Verify API keys are working
2. Check keyword spelling
3. Lower heat score thresholds
4. Increase monitoring frequency

#### High API Usage
1. Increase monitoring interval
2. Reduce number of keywords
3. Use more specific keywords
4. Check API rate limits

### Debug Mode
```bash
# Run with verbose output
python monitor_hot_posts.py once --keywords ai
```

## Advanced Configuration

### Custom Heat Thresholds
Modify `_is_hot_post()` method in `HotPostMonitor` class:

```python
def _is_hot_post(self, post: Dict, platform: str) -> bool:
    heat_score = self._calculate_heat_score(post, platform)
    
    if platform == 'hackernews':
        return heat_score > 200  # Custom threshold
    # ... other platforms
```

### Custom Email Templates
Modify `_create_email_html()` method to customize email appearance.

### Additional Platforms
Extend the system by:
1. Adding new collectors in `src/collectors/`
2. Updating heat score calculation
3. Adding platform-specific criteria

## Security Notes

- Store email passwords securely
- Use app passwords, not regular passwords
- Consider using environment variables
- Regularly rotate API keys
- Monitor for unusual activity

## Performance Tips

- Use specific keywords to reduce noise
- Adjust monitoring frequency based on needs
- Monitor during relevant time zones
- Use multiple email addresses for different topics
- Consider using a dedicated monitoring server

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Test individual components
4. Create an issue on GitHub


