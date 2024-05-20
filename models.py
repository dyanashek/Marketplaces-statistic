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
        self._list_name = list_name
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

        curr_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=settings.TIMEDELTA_MSK)).strftime("%d.%m.%y %H:%M")
        for row in rows:
            self._set_value(row, 
                            8, 
                            curr_time,
                            )

    def _set_value(self, row, column, value):
        self.work_sheet.update_cell(row, column, value)

    def _set_range(self, milvane, elastik):

        if self._list_name == config.WB_LIST:
            range_milvane = f'G4:BU{3 + len(milvane)}'
            range_elastik = f'G{len(milvane) + 9}:BU{len(milvane) + 8 + len(elastik)}'
        else:
            range_milvane = f'G4:AD{3 + len(milvane)}'
            range_elastik = f'G{len(milvane) + 9}:AD{len(milvane) + 8 + len(elastik)}'

        return range_milvane, range_elastik

    def _set_range_values(self, calls_range, values):
        self.work_sheet.update(calls_range, values)

    def update_data(self, milvane_data=[], elastik_data=[]):
        self._get_values()
        self._set_date()
 
        milvane, elastik = self._split_values()
        range_milvane, range_elastik = self._set_range(milvane, elastik)

        if self._list_name == config.WB_LIST:
            coeff = 67
        else:
            coeff = 24

        milvane_final_data = []
        for article in milvane:
            if article in milvane_data:
                milvane_final_data.append(milvane_data[article])
            else:
                milvane_final_data.append(['-',] * coeff)
        
        elastik_final_data = []
        for article in elastik:
            if article in elastik_data:
                elastik_final_data.append(elastik_data[article])
            else:
                elastik_final_data.append(['-',] * coeff)
        
        self._set_range_values(milvane_final_data, range_milvane)
        self._set_range_values(elastik_final_data, range_elastik)


class Wb:
    STORAGE_API_LINK = settings.WB_STAT_API_MAIN_PATH + settings.WB_STORAGE_API_PATH
    SALES_API_LINK = settings.WB_STAT_API_MAIN_PATH + settings.WB_SALES_API_PATH
    INCOME_API_LINK = settings.WB_STAT_API_MAIN_PATH + settings.WB_INCOME_API_PATH
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
                if article not in remains:
                    remains[article] = settings.WB_STORAGES.copy()
                
                remains[article]['total'] += remain
                if storage in settings.wb_warehouses:
                    remains[article][storage] += remain
        
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
            storage = sale.get('warehouseName')

            if sale_id and sale_id.startswith('S'):
                if article not in sales:
                    sales[article] = settings.WB_STORAGES.copy()
                
                sales[article]['total'] += 1
                if storage in settings.wb_warehouses:
                    sales[article][storage] += 1

        return sales
    
    def _get_incomes(self):
        response = requests.get(self.INCOME_API_LINK, headers=self.header, params=self.STORAGE_PARAMS)
        
        return response.json()
    
    def _count_incomes(self):
        incomes_ids = set()
        incomes = {}

        for income in reversed(self._get_incomes()):
            if income.get('status') and income.get('status') == 'Принято':
                incomes_ids.add(income.get('incomeId'))

                if len(incomes_ids) > settings.INCOMES_AMOUNT:
                    break

                article = income.get('barcode')
                quantity = income.get('quantity')

                if article not in incomes:
                    incomes[article] = 0
                incomes[article] += quantity
        
        return incomes

    def combine_sales_remains(self):
        sales = self._count_sales()
        remains = self._count_remains()
        incomes = self._count_incomes()

        report = {}

        for article, remain in remains.items():
            if article in incomes:
                income = incomes[article]
            else:
                income = 0

            if article in sales:
                data = [remain['total'], sales[article]['total'], income,]
                for warehouse in settings.wb_warehouses:
                    if warehouse != 'total':
                        data.append(remain[warehouse])
                        data.append(sales[article][warehouse])
            else:
                data = [remain['total'], 0, income,]
                for warehouse in settings.wb_warehouses:
                    if warehouse != 'total':
                        data.append(remain[warehouse])
                        data.append(0)
            
            report[article] = data
        
        for article, sale in sales.items():
            if article in incomes:
                income = incomes[article]
            else:
                income = 0

            if article not in report:
                data = [0, sale, income]
                for warehouse in settings.wb_warehouses:
                    if warehouse != 'total':
                        data.append(0)
                        data.append(sale[warehouse])

                report[article] = data

        return report


class Ozon:
    STORAGE_API_LINK = settings.OZON_STAT_API_MAIN_PATH + settings.OZON_STORAGE_API_PATH
    SALES_API_LINK = settings.OZON_STAT_API_MAIN_PATH + settings.OZON_SALES_API_PATH
    INCOME_API_LINK = settings.OZON_STAT_API_MAIN_PATH + settings.OZON_INCOME_API_PATH
    PRODUCTS_IN_INCOME_API_PATH = settings.OZON_STAT_API_MAIN_PATH + settings.OZON_PRODUCTS_IN_INCOME_API_PATH
    
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
            storage = product.get('warehouse_name').replace('_', ' ')

            if article not in remains:
                remains[article] = settings.OZON_STORAGES.copy()
            
            remains[article]['total'] += remain
            if storage in settings.ozon_warehouses:
                remains[article][storage] += remain
        
        return remains
    
    def _count_sales(self):
        sales = {}

        for sale in self._get_sales().get('result').get('data'):
            article = sale.get('dimensions')[0].get('id')
            sales_amount = sale.get('metrics')[0]

            sales[article] = sales_amount

        return sales

    def _get_incomes(self):
        params = {
            "page": 1,
            "page_size": settings.INCOMES_AMOUNT,
            "states": ["COMPLETED"],
        }

        response = requests.post(self.INCOME_API_LINK, headers=self.header, json=params)

        return response.json()
    
    def _get_products_in_income(self, income_id, page=1):
        params = {
            "page": page,
            "page_size": 100,
            "supply_order_id": income_id,
        }

        response = requests.post(self.PRODUCTS_IN_INCOME_API_PATH, headers=self.header, json=params)

        return response.json()
    
    def _count_incomes(self):
        incomes = self._get_incomes().get('supply_orders')

        incomes_products = {}
        for income in incomes:
            next_page = True
            page = 1

            while next_page:
                income_info = self._get_products_in_income(income.get('supply_order_id'), page)
                for product in income_info.get('items'):
                    article = str(product.get('sku'))
                    quantity = product.get('quantity')

                    if article not in incomes_products:
                        incomes_products[article] = 0
                    
                    incomes_products[article] += quantity
                
                page += 1
                next_page = income_info.get('has_next')

        return incomes_products

    def combine_sales_remains(self):
        sales = self._count_sales()
        remains = self._count_remains()
        incomes = self._count_incomes()

        report = {}

        for article, remain in remains.items():
            if article in incomes:
                income = incomes[article]
            else:
                income = 0

            if article in sales:
                data = [remain['total'], sales[article], income,]
                for warehouse in settings.ozon_warehouses:
                    if warehouse != 'total':
                        data.append(remain[warehouse])
            else:
                data = [remain['total'], 0, income, *[0] * (len(settings.ozon_warehouses) - 1)]
            
            report[article] = data
        
        for article, sale in sales.items():
            if article in incomes:
                income = incomes[article]
            else:
                income = 0

            if article not in report:
                report[article] = [0, sale, income, *[0] * (len(settings.ozon_warehouses) - 1)]
        
        return report



# e = Wb(config.WB_TOKEN1).combine_sales_remains()
# m = Wb(config.WB_TOKEN2).combine_sales_remains()
# Gspread(config.WB_LIST).update_data(m, e)

# e = Ozon(config.OZON_TOKEN1, config.OZON_ID1).combine_sales_remains()
# m = Ozon(config.OZON_TOKEN2, config.OZON_ID2).combine_sales_remains()
# Gspread(config.OZON_LIST).update_data(m, e)
