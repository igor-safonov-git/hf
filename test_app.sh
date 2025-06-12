source venv/bin/activate
# Test environment variables (using dummy values for testing)
export HF_TOKEN="test_token"
export ACC_ID="test_account"
export OPENAI_API_KEY="test_openai_key"

# Run a quick test of the FastAPI app
echo "Testing FastAPI app import..."
python3 -c "
import sys
sys.path.insert(0, \"/home/igor/hf\")
try:
    from app import app, HuntflowClient
    print(\"✅ FastAPI app imports successfully\")
    print(\"✅ HuntflowClient class available\") 
    
    # Test environment variables
    import os
    print(f\"HF_TOKEN: {os.getenv('HF_TOKEN', 'Not set')}\")
    print(f\"ACC_ID: {os.getenv('ACC_ID', 'Not set')}\") 
    print(f\"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'Not set')[:10]}...\")
except ImportError as e:
    print(f\"❌ Import error: {e}\")
except Exception as e:
    print(f\"❌ Error: {e}\")
"
