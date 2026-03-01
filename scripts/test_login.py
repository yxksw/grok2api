"""
测试登录接口
"""

import requests

url = "https://grok.050815.xyz/v1/admin/verify"
headers = {
    "Authorization": "Bearer qweasdzxc123"
}

print(f"Testing: {url}")
print(f"Headers: {headers}")

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
