from time import perf_counter
import requests

print("Starting test...")

start = perf_counter()

response = requests.post(
    "http://127.0.0.1:8000/chat",
    json={
        "prompt": "What is machine learning?"
    }
)

latency = perf_counter() - start

print("Status Code:", response.status_code)
print("Latency:", latency, "seconds")