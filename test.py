import requests

url = "https://api.ataix.kz/api/user/balances/USDT"
headers = {
    "accept": "application/json",
    "X-API-Key": "jMO7HnaoAPg2i6DJIujrPf4al10xIfJbkqyWjmVrGwCA3jNPRs9bxfsJlZlYdHc6RZfFPYRK77MBqcQjtvQ1H1"  # API кілтіңізді қойыңыз
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()  # JSON жауабын сөздікке айналдыру
    available_usdt = data['result']['available']  # available мәнін алу
    print("USDT қолжетімді сомасы:", available_usdt)
else:
    print("Қате пайда болды:", response.status_code, response.text)

