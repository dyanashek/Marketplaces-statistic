import requests
import pprint
import datetime
import gspread

import settings
import config


class Gspread:
    service_acc = gspread.service_account(filename='service_account.json')
    sheet = service_acc.open(config.SPREAD_NAME)

    def __init__(self, list_name):
        self.work_sheet = self.sheet.worksheet(list_name)

    def _get_values(self):
        self.values = self.work_sheet.get_all_values()

    def _split_values(self):
        milvane = []
        elastik = []

        ELASTIK_FLAG = False
        for value in self.values:
            if value[2].lower() == 'elastik':
                ELASTIK_FLAG = True

            if value[1].isdigit():
                if ELASTIK_FLAG: 
                    elastik.append(value[1])
                else:
                    milvane.append(value[1])

        return milvane, elastik

    def _get_date_cells(self):
        rows = []

        for num, value in enumerate(self.values):
            if 'дата' in value:
                rows.append(num + 1)
        
        return rows
    
    def _set_date(self):
        rows = self._get_date_cells()

        for row in rows:
            self._set_value(row, 8, str(datetime.date.today()))

    def _set_value(self, row, column, value):
        self.work_sheet.update_cell(row, column, value)

    def _set_range(self, milvane, elastik):

        range_milvane = f'G4:H{3 + len(milvane)}'
        range_elastik = f'G{len(milvane) + 9}:H{len(milvane) + 8 + len(elastik)}'

        return range_milvane, range_elastik

    def _set_range_values(self, calls_range, values):
        self.work_sheet.update(calls_range, values)

    def update_data(self, milvane_data=[], elastik_data=[]):
        self._get_values()
        self._set_date()
        
        milvane, elastik = self._split_values()
        range_milvane, range_elastik = self._set_range(milvane, elastik)

        milvane_final_data = []
        for article in milvane:
            if article in milvane_data:
                milvane_final_data.append(milvane_data[article])
            else:
                milvane_final_data.append(('-', '-',))
        
        elastik_final_data = []
        for article in elastik:
            if article in elastik_data:
                elastik_final_data.append(elastik_data[article])
            else:
                elastik_final_data.append(('-', '-',))
        
        self._set_range_values(milvane_final_data, range_milvane)
        self._set_range_values(elastik_final_data, range_elastik)


class Wb:
    STORAGE_API_LINK = settings.WB_STAT_API_MAIN_PATH + settings.WB_STORAGE_API_PATH
    SALES_API_LINK = settings.WB_STAT_API_MAIN_PATH + settings.WB_SALES_API_PATH
    STORAGE_PARAMS = {
            'dateFrom' : settings.WB_STORAGE_DATE_FROM,
        }

    def __init__(self, token):
        self.header = {'Authorization': token}

    @staticmethod
    def _get_sales_report_period():
        date_to = datetime.datetime.utcnow() + datetime.timedelta(hours=settings.TIMEDELTA_MSK)
        date_from = date_to - datetime.timedelta(days=settings.REPORT_PERIOD)
        
        return date_from.strftime('%Y-%m-%dT%H:%M:%S')
    
    def _get_remain_stock(self):
        response = requests.get(self.STORAGE_API_LINK, headers=self.header, params=self.STORAGE_PARAMS)
        
        return response.json()
    
    def _count_remains(self):
        remains = {}

        for product in self._get_remain_stock():
            article = product.get('barcode')
            storage = product.get('warehouseName')
            remain = product.get('quantity')

            if storage and storage not in settings.WB_STORAGE_EXCEPTIONS:
                if article in remains:
                    remains[article] += remain
                else:
                    remains[article] = remain
        
        return remains
    
    def _get_sales(self):
        date_from = self._get_sales_report_period()
        params = {
            'dateFrom' : date_from,
        }

        response = requests.get(self.SALES_API_LINK, headers=self.header, params=params)

        return response.json()
    
    def _count_sales(self):
        sales = {}

        for sale in self._get_sales():
            article = sale.get('barcode')
            sale_id = sale.get('saleID')

            if sale_id and sale_id.startswith('S'):
                if article in sales:
                    sales[article] += 1
                else:
                    sales[article] = 1

        return sales
    
    def combine_sales_remains(self):
        sales = self._count_sales()
        remains = self._count_remains()

        report = {}

        for article, remain in remains.items():
            if article in sales:
                report[article] = (remain, sales[article],)
            else:
                report[article] = (remain, 0,)
        
        for article, sale in sales.items():
            if article not in report:
                report[article] = (0, sale)
        
        return report


class Ozon:
    STORAGE_API_LINK = settings.OZON_STAT_API_MAIN_PATH + settings.OZON_STORAGE_API_PATH
    SALES_API_LINK = settings.OZON_STAT_API_MAIN_PATH + settings.OZON_SALES_API_PATH

    def __init__(self, token, client_id):
        self.header = {
                        'Client-Id' : client_id,
                        'Api-Key' : token,
                    }
    
    @staticmethod
    def _get_sales_report_period():
        date_to = datetime.datetime.utcnow() + datetime.timedelta(hours=settings.TIMEDELTA_MSK)
        date_from = date_to - datetime.timedelta(days=settings.REPORT_PERIOD)
        
        return date_from.strftime('%Y-%m-%dT%H:%M:%S'), date_to.strftime('%Y-%m-%dT%H:%M:%S')
    
    def _get_remain_stock(self):
        params = {
            'limit' : 1000,
        }
        response = requests.post(self.STORAGE_API_LINK, headers=self.header, json=params)
        
        return response.json()
    
    def _get_sales(self):
        date_from, date_to = self._get_sales_report_period()
        params = {
            'date_from' : date_from,
            'date_to' : date_to,
            'dimension' : ['sku',],
            'limit' : 1000,
            'metrics' : ['ordered_units',],
        }

        response = requests.post(self.SALES_API_LINK, headers=self.header, json=params)

        return response.json()
    
    def _count_remains(self):
        remains = {}

        for product in self._get_remain_stock().get('result').get('rows'):
            article = str(product.get('sku'))
            remain = product.get('free_to_sell_amount')

            if article in remains:
                remains[article] += remain
            else:
                remains[article] = remain
        
        return remains
    
    def _count_sales(self):
        sales = {}

        for sale in self._get_sales().get('result').get('data'):
            article = sale.get('dimensions')[0].get('id')
            sales_amount = sale.get('metrics')[0]

            sales[article] = sales_amount

        return sales

    def combine_sales_remains(self):
        sales = self._count_sales()
        remains = self._count_remains()

        report = {}

        for article, remain in remains.items():
            if article in sales:
                report[article] = (remain, sales[article],)
            else:
                report[article] = (remain, 0,)
        
        for article, sale in sales.items():
            if article not in report:
                report[article] = (0, sale)
        
        return report
