import requests

# Make a web request to the API Gateway
api_gateway_url = "https://4wvm0o3xmb.execute-api.us-east-1.amazonaws.com/prod/submit_tournament"
payload = {"name": "John Doe", "file_path": "test_file.txt", "school": "Test School", "tournament": "12345",}
response = requests.post(api_gateway_url, json=payload)
print((response.content))
