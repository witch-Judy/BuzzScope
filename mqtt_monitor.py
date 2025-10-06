#!/usr/bin/env python3
"""
MQTT Monitor Script
Subscribe to BuzzScope MQTT topics and display messages
"""
import sys
import os
import json
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MQTTMonitor:
    """Monitor MQTT messages from BuzzScope"""
    
    def __init__(self):
        self.client = None
        self.connected = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects"""
        if rc == 0:
            print("✅ Connected to MQTT broker")
            self.connected = True
            
            # Subscribe to all BuzzScope topics
            client.subscribe("buzzscope/alerts/+", qos=1)
            print("📡 Subscribed to buzzscope/alerts/+")
        else:
            print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects"""
        print("🔌 Disconnected from MQTT broker")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback for when message is received"""
        try:
            # Parse JSON message
            data = json.loads(msg.payload.decode())
            
            print(f"\n🔔 New Alert!")
            print(f"📱 Platform: {data.get('platform', 'Unknown').upper()}")
            print(f"🔍 Keyword: {data.get('keyword', 'Unknown')}")
            print(f"⏰ Found at: {data.get('found_at', 'Unknown')}")
            
            post = data.get('post', {})
            print(f"📝 Title: {post.get('title', 'No title')[:80]}...")
            print(f"👤 Author: {post.get('author', 'Unknown')}")
            print(f"📊 Score: {post.get('score', 0)}")
            print(f"🔗 URL: {post.get('url', 'No URL')}")
            print("-" * 60)
            
        except json.JSONDecodeError:
            print(f"📨 Raw message on {msg.topic}: {msg.payload.decode()}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def start_monitoring(self, broker="localhost", port=1883):
        """Start monitoring MQTT messages"""
        print("🔍 BuzzScope MQTT Monitor")
        print("=" * 50)
        print(f"Broker: {broker}:{port}")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        # Create client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        try:
            # Connect to broker
            self.client.connect(broker, port, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if self.client:
                self.client.disconnect()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor BuzzScope MQTT messages')
    parser.add_argument('--broker', default='localhost',
                       help='MQTT broker address (default: localhost)')
    parser.add_argument('--port', type=int, default=1883,
                       help='MQTT broker port (default: 1883)')
    
    args = parser.parse_args()
    
    monitor = MQTTMonitor()
    monitor.start_monitoring(args.broker, args.port)

if __name__ == "__main__":
    main()
