# MQTT Setup Guide

## 🔧 MQTT Broker Options

BuzzScope supports any standard MQTT broker. Here are the most common options:

### 1. Local MQTT Broker (Eclipse Mosquitto)

**Quick Setup with Docker:**
```bash
# Run Mosquitto broker locally
docker run -it -p 1883:1883 -p 9001:9001 eclipse-mosquitto

# Or with persistent data
docker run -d --name mosquitto -p 1883:1883 -p 9001:9001 -v mosquitto_data:/mosquitto/data eclipse-mosquitto
```

**Configuration:**
```bash
# In your .env file
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USE_TLS=false
```

### 2. HiveMQ Cloud (Recommended for Production)

**Sign up:** https://www.hivemq.com/cloud/

**Configuration:**
```bash
# In your .env file
MQTT_BROKER=your-cluster-id.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=your_hivemq_username
MQTT_PASSWORD=your_hivemq_password
MQTT_USE_TLS=true
```

### 3. AWS IoT Core

**Setup:** https://aws.amazon.com/iot-core/

**Configuration:**
```bash
# In your .env file
MQTT_BROKER=your-endpoint.iot.region.amazonaws.com
MQTT_PORT=8883
MQTT_USERNAME=your_aws_username
MQTT_PASSWORD=your_aws_password
MQTT_USE_TLS=true
```

### 4. Azure IoT Hub

**Setup:** https://azure.microsoft.com/en-us/services/iot-hub/

**Configuration:**
```bash
# In your .env file
MQTT_BROKER=your-hub.azure-devices.net
MQTT_PORT=8883
MQTT_USERNAME=your_azure_username
MQTT_PASSWORD=your_azure_password
MQTT_USE_TLS=true
```

## 🧪 Testing MQTT Connection

### Test Script
```bash
# Test all configured MQTT brokers
python test_mqtt_connection.py
```

### Manual Test
```bash
# Test with specific broker
python monitor_keywords.py "test" --once --mqtt-broker localhost --mqtt-port 1883
```

## 📡 MQTT Topics

BuzzScope publishes to the following topic structure:

```
buzzscope/alerts/{keyword}
```

**Examples:**
- `buzzscope/alerts/unified namespace`
- `buzzscope/alerts/ai`
- `buzzscope/alerts/iot`

## 📨 Message Format

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

## 🔒 Security Best Practices

### Authentication
- Always use username/password for production
- Use strong, unique passwords
- Rotate credentials regularly

### TLS/SSL
- Enable TLS for production deployments
- Use port 8883 for secure connections
- Verify certificate validity

### Network Security
- Use VPN for remote access
- Restrict broker access to trusted IPs
- Monitor connection logs

## 🚀 Production Deployment

### HiveMQ Cloud (Recommended)
1. Sign up for HiveMQ Cloud
2. Create a cluster
3. Generate credentials
4. Configure in `.env`:
   ```bash
   MQTT_BROKER=your-cluster.hivemq.cloud
   MQTT_PORT=8883
   MQTT_USERNAME=your_username
   MQTT_PASSWORD=your_password
   MQTT_USE_TLS=true
   ```

### Self-Hosted
1. Set up Mosquitto with authentication
2. Configure TLS certificates
3. Set up monitoring and logging
4. Configure in `.env`:
   ```bash
   MQTT_BROKER=your-broker.domain.com
   MQTT_PORT=8883
   MQTT_USERNAME=your_username
   MQTT_PASSWORD=your_password
   MQTT_USE_TLS=true
   ```

## 🔧 Troubleshooting

### Connection Issues
```bash
# Test basic connectivity
telnet your-broker.com 1883

# Test with TLS
openssl s_client -connect your-broker.com:8883
```

### Authentication Issues
- Verify username/password
- Check broker authentication settings
- Ensure user has publish permissions

### TLS Issues
- Verify certificate validity
- Check TLS version compatibility
- Ensure proper port (8883 for TLS)

### Firewall Issues
- Open required ports (1883/8883)
- Check outbound connection rules
- Verify proxy settings

## 📊 Monitoring

### MQTT Client Logs
```bash
# Enable debug logging
export MQTT_LOG_LEVEL=DEBUG
python monitor_keywords.py "keyword" --once
```

### Broker Metrics
- Connection count
- Message throughput
- Error rates
- Client disconnections

### Application Metrics
- Notification success rate
- MQTT publish failures
- Connection retry attempts
