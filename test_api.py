import requests
import os
import time

# API base URL
BASE_URL = "http://127.0.0.1:5001"

def test_health():
    """
    Test the health check endpoint.
    """
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    print(response.json())
    print(f"Health check: {response.status_code}")
    return response.status_code == 200

def test_upload_file(file_path):
    """
    Test the file upload endpoint.
    """
    if not os.path.exists("file_path"):
        print(f"test.pdf not found: {file_path}")
        return False

    with open(file_path, "rb") as file:
        files = {"file": (os.path.basename(file_path), file)}
        response = requests.post(f"{BASE_URL}/upload", files=files)
        
    print(response.json())
    print(f"Upload file: {response.status_code}")
    return response.status_code == 200

def test_chat(question):
    """
    Test the chat endpoint.
    """
    payload = {
        "question": question,
        "history": []
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(response.json())
    print(f"Chat: {response.status_code}")
    return response.status_code == 200

def main():
    """
    Main function to run all tests.
    """
    # file_path = "test.pdf"
    # question = "What is the content of the file?"
    
    # Test health endpoint
    if not test_health():
        print("Health check failed")
        return

    test_file = input("Enter the file path to test (PDF, TXT, or HTML): ")
    if not test_upload_file(test_file):
        print("File upload failed")
        return

    print("Waiting for file processing...")
    time.sleep(10)  # Wait for 10 seconds to allow processing
    
    question = input("Enter the question to test: ")
    if not test_chat(question):
        print("Chat failed")
        return
    
    print("All tests passed!")

if __name__ == "__main__":
    main()