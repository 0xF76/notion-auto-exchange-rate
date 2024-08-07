import json
import requests
from bs4 import BeautifulSoup
from decouple import config

def fetch_currency_rates():
    try:
        r = requests.get('https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html', timeout = 5)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.content, 'html.parser')

        table = soup.find_all('table')[0]
        rows = table.find_all('tr')
        currency_rates = {}
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 1:
                currency_rates[cols[0].text] = float((cols[2].text).strip())
        
        return currency_rates       

    except requests.exceptions.HTTPError as errh:
        print("Http Error:",errh)
        
        return None


def update_notion_page(page_id, currency_code, exchange_rate, headers):
    url = f'https://api.notion.com/v1/pages/{page_id}'
    data = {
        "properties": {
            "Exchange Rate": {
                "number": exchange_rate
            }
        }
    }

    try:
        response = requests.patch(url, headers=headers, data=json.dumps(data), timeout=5)
        if response.status_code == 200:
            print(f"Exchange rate for {currency_code} updated successfully")
        else:
            print(f"Error updating exchange rate for {currency_code}: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as err:
        print(f"Error updating exchange rate for {currency_code}: {err}")

        
def main():
    database_id = config('NOTION_DATABASE_ID')
    notion_token = config("NOTION_TOKEN")
    url = f'https://api.notion.com/v1/databases/{database_id}/query'


    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, timeout=5)
        response.raise_for_status()

        exhange_rates = fetch_currency_rates()
        if exhange_rates is None:
            return

        pages = response.json()['results']

        for page in pages:
            page_id = page['id']
            currency_code = page['properties']['Currency Code']['title'][0]['text']['content']
            if currency_code in exhange_rates:
                exchange_rate = exhange_rates[currency_code]
                update_notion_page(page_id, currency_code, exchange_rate, headers)
    except requests.exceptions.HTTPError as errh:
        print("Http Error:",errh)


if __name__ == '__main__':
    main()
