# 🔥 Hot Post Monitor Guide

## Overview

The Hot Post Monitor is an independent system running on port 8503 that automatically detects trending posts across Hacker News, Reddit, and YouTube, and sends email notifications when hot posts are found.

## Features

- **Real-time Detection**: Monitors multiple platforms simultaneously
- **Smart Heat Scoring**: Uses advanced algorithms to detect trending content
- **Email Notifications**: Sends beautiful HTML emails with post details
- **Configurable Thresholds**: Customizable criteria for hot posts
- **Multiple Keywords**: Monitor multiple keywords simultaneously
- **Independent Operation**: Runs separately from main apps (8501, 8502)

## Access

### Web Interface
- **URL**: http://localhost:8503
- **Purpose**: Manual monitoring and configuration
- **Features**: 
  - Configure keywords and platforms
  - Run one-time detection
  - Test email functionality
  - View monitoring results

### Command Line Service
- **Purpose**: Automated monitoring and scheduling
- **Features**:
  - Run once: `python3 hot_post_monitor_service.py once`
  - Schedule monitoring: `python3 hot_post_monitor_service.py schedule --interval 30`

## Configuration

### Keywords
Default keywords: `ai, iot, mqtt, unified_namespace`
- Can be customized in the web interface
- Supports comma-separated values
- Case-insensitive matching

### Time Range
Default time range: 24 hours (1 day)
- Fixed to 24 hours for optimal hot post detection
- All platforms search for posts from the last 24 hours
- Provides better coverage of trending content

### Platforms
- **Hacker News**: Real-time API access
- **Reddit**: Public JSON API
- **YouTube**: Data API v3 (requires API key)

### Hot Post Criteria

#### Hacker News
- Heat Score > 150 OR
- Score > 100 OR
- Comments > 50

#### Reddit
- Heat Score > 1000 OR
- Score > 500 OR
- Comments > 100

#### YouTube
- Heat Score > 2000 OR
- Views > 10,000 OR
- Likes > 1,000 OR
- Comments > 50

## Heat Score Calculation

```
Hacker News: score + (comments × 2)
Reddit: score + (comments × 1.5)
YouTube: (views ÷ 100) + likes + (comments × 2)
```

## Email Notifications

### Configuration
Email settings are loaded from `.env` file:
```env
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
TO_EMAIL=notifications@yourdomain.com
```

### Email Content
Each notification includes:
- Number of hot posts detected
- Post title (clickable link)
- Platform and metrics
- Heat score
- Author and timestamp
- Keyword that triggered the alert

### HTML Email Features
- Professional design
- Clickable links
- Platform badges
- Heat score indicators
- Responsive layout

## Usage Examples

### Manual Monitoring
1. Open http://localhost:8503
2. Configure keywords and platforms
3. Click "Run Hot Post Detection"
4. Review results
5. Send email notification if needed

### Automated Monitoring
```bash
# Run once
python3 hot_post_monitor_service.py once

# Schedule every 30 minutes
python3 hot_post_monitor_service.py schedule --interval 30

# Schedule every hour
python3 hot_post_monitor_service.py schedule --interval 60
```

### Testing
```bash
# Test email functionality
# Use the "Test Email" button in the web interface
```

## Monitoring Logs

### Log File
- **Location**: `data/monitoring/hot_post_log.json`
- **Content**: Timestamp, post count, keywords, platforms, email status

### Log Entry Example
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "hot_posts_count": 3,
  "keywords": ["ai", "iot", "mqtt", "unified_namespace"],
  "platforms": ["hackernews", "reddit", "youtube"],
  "email_sent": true
}
```

## API Requirements

### Hacker News
- **API**: Free public API
- **Rate Limit**: No official limit
- **Data**: Top stories, comments, scores

### Reddit
- **API**: Free public JSON API
- **Rate Limit**: 60 requests per minute
- **Data**: Posts, comments, scores

### YouTube
- **API**: YouTube Data API v3
- **Rate Limit**: 10,000 units per day
- **Setup**: Requires API key in `.env`

## Troubleshooting

### Common Issues

#### No Posts Found
1. Check keyword spelling
2. Verify time range (default: 6 hours)
3. Lower heat score thresholds
4. Check API connectivity

#### Email Not Sending
1. Verify Gmail app password
2. Check SMTP settings
3. Test with "Test Email" button
4. Check firewall/network settings

#### API Errors
1. **YouTube**: Verify API key and quota
2. **Reddit**: Check rate limits
3. **Hacker News**: Usually reliable, check network

### Debug Mode
```bash
# Run with verbose output
python3 hot_post_monitor_service.py once
```

## Performance Tips

### Optimization
- Use specific keywords to reduce noise
- Adjust monitoring frequency based on needs
- Monitor during relevant time zones
- Use appropriate heat score thresholds

### Resource Usage
- **Memory**: Low (caches minimal data)
- **CPU**: Low (periodic API calls)
- **Network**: Moderate (API requests)
- **Storage**: Minimal (log files only)

## Security Notes

- Store email passwords securely
- Use app passwords, not regular passwords
- Monitor API usage and costs
- Regularly rotate API keys
- Check logs for unusual activity

## Integration

### With Main Apps
- **Port 8501**: Historical analysis (unaffected)
- **Port 8502**: New keyword testing (unaffected)
- **Port 8503**: Hot post monitoring (independent)

### Data Sharing
- No shared cache files
- Independent operation
- Separate log files
- No interference with main functionality

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Test individual components
4. Check API connectivity
5. Verify email configuration

## Future Enhancements

- Discord integration
- MQTT notifications
- Webhook support
- Advanced filtering
- Custom heat algorithms
- Multi-user support
