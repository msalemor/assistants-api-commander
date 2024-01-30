import yfinance as yf
import requests


def get_stock_price(symbol: str) -> float:
    stock = yf.Ticker(symbol)
    price = stock.history(period="1d")['Close'].iloc[-1]
    return price


def send_logic_apps_email(email_url: str, to: str, content: str):
    json_payload = {'to': to, 'content': content}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(email_url, json=json_payload, headers=headers)
    if response.status_code == 202:
        print("Email sent to: " + json_payload['to'])
