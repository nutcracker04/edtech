import requests
import json

api_key = "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"
url = "https://integrate.api.nvidia.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

model = "meta/llama-3.2-11b-vision-instruct"
print(f"Testing connectivity for: {model}")

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 10
}

try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print(response.text[:200])
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
