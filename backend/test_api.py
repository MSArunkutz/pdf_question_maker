import requests

def test_api():
    url = "http://localhost:8000/api/generate-questions"
    try:
        with open("test_backend.pdf", "rb") as f:
            files = {"file": ("test_backend.pdf", f, "application/pdf")}
            print(f"Sending request to {url}...")
            response = requests.post(url, files=files)
            
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.json())
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_api()
