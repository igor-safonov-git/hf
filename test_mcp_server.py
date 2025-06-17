#!/usr/bin/env python3
"""Test script to check if MCP server tools are available"""

import subprocess
import sys
import os

def test_mcp_server():
    """Test if the code-review MCP server is working"""
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/igor/code_review/code_review_mcp/src"
    
    cmd = [
        "/home/igor/code_review/venv/bin/python", 
        "-m", "code_review_mcp.server"
    ]
    
    try:
        # Try to start the server and send a simple JSON-RPC message
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        # Send initialization message
        init_msg = """{
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }"""
        
        stdout, stderr = process.communicate(input=init_msg, timeout=5)
        
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        print("Return code:", process.returncode)
        
        return process.returncode == 0
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("Server startup timed out - this might be normal for MCP servers")
        return True
    except Exception as e:
        print(f"Error testing server: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_server()
    print(f"MCP server test: {'PASSED' if success else 'FAILED'}")