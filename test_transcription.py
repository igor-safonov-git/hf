#!/usr/bin/env python3
"""
Test script for OpenAI transcription endpoint
"""
import requests
import io
import os

def test_transcription_endpoint():
    """Test the /transcribe endpoint"""
    url = "http://localhost:8000/transcribe"
    
    # Create a minimal test file (we don't have actual audio, just test the endpoint structure)
    test_data = b"fake audio data for testing"
    
    files = {
        'audio': ('test.webm', io.BytesIO(test_data), 'audio/webm')
    }
    
    try:
        response = requests.post(url, files=files, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if 'success' in result:
                print("✅ Endpoint structure is correct")
                if not result['success']:
                    print(f"Expected error (no real audio): {result.get('error', 'No error message')}")
            else:
                print("❌ Missing 'success' field in response")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Testing OpenAI transcription endpoint...")
    test_transcription_endpoint()