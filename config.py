import os
from dotenv import load_dotenv


load_dotenv()


WB_TOKEN1 = os.getenv('WB_TOKEN1')
WB_TOKEN2 = os.getenv('WB_TOKEN2')

OZON_ID1 = os.getenv('OZON_ID1')
OZON_ID2 = os.getenv('OZON_ID2')
OZON_TOKEN1 = os.getenv('OZON_TOKEN1')
OZON_TOKEN2 = os.getenv('OZON_TOKEN2')

SPREAD_NAME = 'marketplaces_stats'
WB_LIST = 'WB'
OZON_LIST = 'Ozon'

GSPREAD_CONFIG = 'service_account.json'

