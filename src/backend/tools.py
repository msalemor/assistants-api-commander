import html
from pydantic import BaseModel
import yfinance as yf
import requests
import logging


def get_stock_price(symbol: str) -> float:
    logging.info(f"Getting stock price for {symbol}")
    stock = yf.Ticker(symbol)
    price = stock.history(period="1d")['Close'].iloc[-1]
    return price


def send_logic_apps_email(email_url: str, to: str, content: str):
    try:
        logging.info(f"Sending email to {to}")
        json_payload = {'to': to, 'content':  html.unescape(content)}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(email_url, json=json_payload, headers=headers)
        if response.status_code == 202:
            print("Email sent to: " + json_payload['to'])
    except Exception as e:
        logging.error(f"Unable to send email due to {e}")


class Country:
    def __init__(self, data):
        self.name = data[0]['name']
        self.tld = data[0]['tld']
        self.cca2 = data[0]['cca2']
        self.ccn3 = data[0]['ccn3']
        self.cca3 = data[0]['cca3']
        self.cioc = data[0]['cioc']
        self.independent = data[0]['independent']
        self.status = data[0]['status']
        self.unMember = data[0]['unMember']
        self.currencies = data[0]['currencies']
        self.idd = data[0]['idd']
        self.capital = data[0]['capital']
        self.altSpellings = data[0]['altSpellings']
        self.region = data[0]['region']
        self.subregion = data[0]['subregion']
        self.languages = data[0]['languages']
        self.translations = data[0]['translations']
        self.latlng = data[0]['latlng']
        self.landlocked = data[0]['landlocked']
        self.borders = data[0]['borders']
        self.area = data[0]['area']
        self.demonyms = data[0]['demonyms']
        self.flag = data[0]['flag']
        self.maps = data[0]['maps']
        self.population = data[0]['population']
        self.gini = data[0]['gini']
        self.fifa = data[0]['fifa']
        self.car = data[0]['car']
        self.timezones = data[0]['timezones']
        self.continents = data[0]['continents']
        self.flags = data[0]['flags']
        self.coatOfArms = data[0]['coatOfArms']
        self.startOfWeek = data[0]['startOfWeek']
        self.capitalInfo = data[0]['capitalInfo']
        self.postalCode = data[0]['postalCode']
        self.latitude = data[0]['latitude']
        self.longitude = data[0]['longitude']
        self.areaKm2 = data[0]['areaKm2']
        self.areaMi2 = data[0]['areaMi2']
        self.areaInfo = data[0]['areaInfo']
        self.populationInfo = data[0]['populationInfo']
        self.elevation = data[0]['elevation']
        self.elevationInfo = data[0]['elevationInfo']
        self.demonym = data[0]['demonym']
        self.demonymInfo = data[0]['demonymInfo']
        self.currency = data[0]['currency']
        # self.currencyInfo = data[0]['currencyInfo']
        # self.currencyCode = data[0]['currencyCode']
        # self.currencySubUnit = data[0]['currencySubUnit']
        # self.currencyInfo = data[0]['currencyInfo']
        # self.currencySubUnit = data[0]['currencySubUnit']
        # self.currencySubUnitInfo = data[0]['currencySubUnitInfo']
        # self.currencyFraction = data[0]['currencyFraction']
        # self.currencyFractionInfo = data[0]['currencyFractionInfo']
        # self.currencySymbol = data[0]['currencySymbol']
        # self.currencySymbolInfo = data[0]['currencySymbolInfo']
        # self.currencyDecimals = data[0]['currencyDecimals']
        # self.currencyDecimalsInfo = data[0]['currencyDecimalsInfo']
        # self.currencyThousandsSeparator = data[0]['currencyThousandsSeparator']
        # self.currencyThousandsSeparatorInfo = data[0]['currencyThousandsSeparatorInfo']
        # self.currencyPrefix = data[0]['currencyPrefix']
        # self.currencyPrefixInfo = data[0]['currencyPrefixInfo']
        # self.currencySuffix = data[0]['currencySuffix']
        # self.currencySuffixInfo = data[0]['currencySuffixInfo']


def get_country_data(country: str) -> str:
    resp = requests.get(
        f"https://restcountries.com/v3.1/name/{country}", headers={"Accept": "application/json"})
    resp.raise_for_status()
    country = Country(resp.json())
    return f'Country: {country.name}\nCapital: {country.capital}\nPopulation: {country.population}\nArea: {country.area} km²\nRegion: {country.region}\nSubregion: {country.subregion}'
