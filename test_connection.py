#!/usr/bin/env python3
"""Test script to verify MCP server connection."""

import httpx
import json
import sys

def test_streamable_http():
    """Test connection to streamable-http MCP server."""
    print("Testing MCP server connection...")
    
    # MCP protocol requires specific headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    # Initialize request
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        },
        "id": 1
    }
    
    try:
        # Test connection
        response = httpx.post(
            "http://localhost:8000/mcp",
            headers=headers,
            json=init_request,
            timeout=5.0
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("Success! Server responded correctly.")
            print(f"Response body: {response.text}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except httpx.ConnectError:
        print("Error: Could not connect to server at http://localhost:8000/mcp")
        print("Make sure the server is running.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_streamable_http()