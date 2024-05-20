TIMEDELTA_MSK = 3 #hours
REPORT_PERIOD = 7 #days

UPDATE_TIME = '23:59'
UPDATE_PERIOD = 1 #days
UPDATE_WEEKDAY = 7 #monday-1

INCOMES_AMOUNT = 3

WB_STORAGE_DATE_FROM = '2000-01-01'
WB_STORAGE_EXCEPTIONS = ['Санкт-Петербург Шушары',]

WB_STAT_API_MAIN_PATH = 'https://statistics-api.wildberries.ru/'
WB_STORAGE_API_PATH = 'api/v1/supplier/stocks'
WB_SALES_API_PATH = 'api/v1/supplier/sales'
WB_INCOME_API_PATH = 'api/v1/supplier/incomes'

OZON_STAT_API_MAIN_PATH = 'https://api-seller.ozon.ru/'
OZON_STORAGE_API_PATH = 'v2/analytics/stock_on_warehouses'
OZON_SALES_API_PATH = 'v1/analytics/data'
OZON_INCOME_API_PATH = 'v1/supply-order/list'
OZON_PRODUCTS_IN_INCOME_API_PATH = 'v1/supply-order/items'


wb_warehouses = ('total', 'Электросталь', 'Коледино', 'Подольск', 'Белые Столбы',
     'Белая дача', 'Санкт-Петербург Уткина Заводь', 'Екатеринбург - Испытателей 14г',
     'Казань', 'Тула', 'Краснодар', 'Новосибирск', 'Невинномысск', 'Екатеринбург - Перспективный 12',
     'Хабаровск', 'СЦ Хабаровск', 'Волгоград', 'Обухово',  
     'Рязань (Тюшевское)', 'Минск', 'Крыловская', 'Атакент', 'Чехов 2',
     'Иваново', 'Пушкино', 'Вёшки', 'Чехов 1', 
     'Астана',  'СЦ Кузнецк', 'Новосемейкино',  'Радумля 1', 'СЦ Ижевск',
     'Котовск',)

ozon_warehouses = ('total', 'СОФЬИНО РФЦ', 'КАЛИНИНГРАД МРФЦ', 'ПУШКИНО 1 РФЦ', 'ПУШКИНО 2 РФЦ', 
        'ЖУКОВСКИЙ РФЦ', 'ТВЕРЬ РФЦ', 'Казань РФЦ НОВЫЙ', 'Екатеринбург РФЦ НОВЫЙ', 
        'СПБ ШУШАРЫ РФЦ', 'СПБ БУГРЫ РФЦ', 'Ростов на Дону РФЦ', 'НИЖНИЙ НОВГОРОД РФЦ', 
        'САМАРА РФЦ', 'ХАБАРОВСК 2 РФЦ', 'КРАСНОЯРСК МРФЦ', 'НОВОРОССИЙСК МРФЦ', 
        'НОГИНСК РФЦ', 'ПЕТРОВСКОЕ РФЦ', 'ХОРУГВИНО РФЦ', 'Санкт Петербург РФЦ', 'Новосибирск РФЦ НОВЫЙ',)

WB_STORAGES = {i: 0 for i in wb_warehouses}
OZON_STORAGES = {i: 0 for i in ozon_warehouses}
