import requests
import json
from config import UPDATE_SERVER_PORT, MOCK_GITHUB_PORT

def test_update_server():
    print("\nTesting Update Server...")
    
    # Test health check
    response = requests.get(f"http://localhost:{UPDATE_SERVER_PORT}/health")
    print(f"Health Check: {response.status_code}")
    print(response.json())
    
    # Test manifest
    response = requests.get(f"http://localhost:{UPDATE_SERVER_PORT}/manifest/latest")
    print(f"\nLatest Manifest: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_github_server():
    print("\nTesting GitHub Server...")
    
    # Test health check
    response = requests.get(f"http://localhost:{MOCK_GITHUB_PORT}/health")
    print(f"Health Check: {response.status_code}")
    print(response.json())
    
    # Test latest release
    response = requests.get(f"http://localhost:{MOCK_GITHUB_PORT}/repos/test/test/releases/latest")
    print(f"\nLatest Release: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    try:
        test_update_server()
        test_github_server()
        print("\nAll tests completed successfully!")
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to one or both servers. Make sure they are running!") 