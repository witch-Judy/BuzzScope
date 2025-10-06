#!/usr/bin/env python3
"""
MQTT Connection Test Script
Tests connection to various MQTT brokers including HiveMQ
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

class MQTTTester:
    """Test MQTT connections to various brokers"""
    
    def __init__(self):
        self.connected = False
        self.message_received = False
        self.received_message = None
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects"""
        if rc == 0:
            print("✅ Connected to MQTT broker successfully")
            self.connected = True
        else:
            print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects"""
        print("🔌 Disconnected from MQTT broker")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback for when message is received"""
        print(f"📨 Received message on topic {msg.topic}: {msg.payload.decode()}")
        self.message_received = True
        self.received_message = msg.payload.decode()
    
    def on_publish(self, client, userdata, mid):
        """Callback for when message is published"""
        print(f"📤 Message published successfully (mid: {mid})")
    
    def test_connection(self, broker: str, port: int, username: str = None, 
                       password: str = None, use_tls: bool = False):
        """Test connection to MQTT broker"""
        print(f"🔍 Testing connection to {broker}:{port}")
        print(f"   TLS: {use_tls}")
        print(f"   Auth: {'Yes' if username else 'No'}")
        
        # Create client
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.on_message = self.on_message
        client.on_publish = self.on_publish
        
        try:
            # Configure authentication
            if username and password:
                client.username_pw_set(username, password)
            
            # Configure TLS
            if use_tls:
                client.tls_set()
            
            # Connect
            client.connect(broker, port, 60)
            client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if not self.connected:
                print("❌ Connection timeout")
                return False
            
            # Test publish/subscribe
            test_topic = "buzzscope/test"
            test_message = json.dumps({
                "test": True,
                "timestamp": time.time(),
                "broker": broker
            })
            
            # Subscribe to test topic
            client.subscribe(test_topic, qos=1)
            time.sleep(1)
            
            # Publish test message
            result = client.publish(test_topic, test_message, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("✅ Test message published successfully")
            else:
                print(f"❌ Failed to publish test message: {result.rc}")
                return False
            
            # Wait for message to be received
            time.sleep(2)
            
            if self.message_received:
                print("✅ Test message received successfully")
                return True
            else:
                print("❌ Test message not received")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        finally:
            client.loop_stop()
            client.disconnect()

def test_local_mqtt():
    """Test local MQTT broker"""
    print("\\n🏠 Testing Local MQTT Broker")
    print("=" * 40)
    
    tester = MQTTTester()
    success = tester.test_connection("localhost", 1883)
    
    if success:
        print("✅ Local MQTT broker test PASSED")
    else:
        print("❌ Local MQTT broker test FAILED")
        print("   Make sure you have an MQTT broker running on localhost:1883")
    
    return success

def test_hivemq_cloud():
    """Test HiveMQ Cloud connection"""
    print("\\n☁️ Testing HiveMQ Cloud")
    print("=" * 40)
    
    # Get HiveMQ credentials from environment
    broker = os.getenv('HIVEMQ_BROKER')
    username = os.getenv('HIVEMQ_USERNAME')
    password = os.getenv('HIVEMQ_PASSWORD')
    
    if not all([broker, username, password]):
        print("⚠️ HiveMQ credentials not found in environment variables")
        print("   Set HIVEMQ_BROKER, HIVEMQ_USERNAME, HIVEMQ_PASSWORD")
        return False
    
    tester = MQTTTester()
    success = tester.test_connection(broker, 8883, username, password, use_tls=True)
    
    if success:
        print("✅ HiveMQ Cloud test PASSED")
    else:
        print("❌ HiveMQ Cloud test FAILED")
    
    return success

def test_custom_broker():
    """Test custom MQTT broker from environment"""
    print("\\n🔧 Testing Custom MQTT Broker")
    print("=" * 40)
    
    broker = os.getenv('MQTT_BROKER')
    port = int(os.getenv('MQTT_PORT', '1883'))
    username = os.getenv('MQTT_USERNAME')
    password = os.getenv('MQTT_PASSWORD')
    use_tls = os.getenv('MQTT_USE_TLS', 'false').lower() == 'true'
    
    if not broker or broker == 'localhost':
        print("⚠️ No custom MQTT broker configured")
        return False
    
    tester = MQTTTester()
    success = tester.test_connection(broker, port, username, password, use_tls)
    
    if success:
        print("✅ Custom MQTT broker test PASSED")
    else:
        print("❌ Custom MQTT broker test FAILED")
    
    return success

def main():
    """Run all MQTT tests"""
    print("🔍 BuzzScope MQTT Connection Test")
    print("=" * 50)
    
    tests = [
        ("Local MQTT", test_local_mqtt),
        ("HiveMQ Cloud", test_hivemq_cloud),
        ("Custom Broker", test_custom_broker),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\\nOverall: {passed}/{len(results)} tests passed")
    
    if passed > 0:
        print("\\n🎉 At least one MQTT broker is working!")
        print("\\nNext steps:")
        print("1. Configure your preferred broker in .env")
        print("2. Run: python monitor_keywords.py 'keyword' --once")
    else:
        print("\\n⚠️ No MQTT brokers are working.")
        print("\\nTroubleshooting:")
        print("1. Install MQTT broker locally: docker run -p 1883:1883 eclipse-mosquitto")
        print("2. Or sign up for HiveMQ Cloud: https://www.hivemq.com/cloud/")
        print("3. Or use any other MQTT broker service")

if __name__ == "__main__":
    main()
