import time
import logging
import datetime
import inspect

import config
import settings
from models import Gspread, Wb, Ozon


logging.basicConfig(level=logging.ERROR, 
                    filename="py_log.log", 
                    filemode="w", 
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    )


def parse_data():
    wb_spread = Gspread(config.WB_LIST)
    ozon_spread = Gspread(config.OZON_LIST)

    wb_elastik = Wb(config.WB_TOKEN1)
    wb_milvane = Wb(config.WB_TOKEN2)

    ozon_elastik = Ozon(config.OZON_TOKEN1, config.OZON_ID1)
    ozon_milvane = Ozon(config.OZON_TOKEN2, config.OZON_ID2)

    while True:
        curr = datetime.datetime.utcnow() + datetime.timedelta(hours=settings.TIMEDELTA_MSK)
        current_time = curr.strftime("%H:%M")

        if current_time == settings.UPDATE_TIME:
            try:
                elastik = wb_elastik.combine_sales_remains()
            except Exception as ex:
                logging.error(f'{inspect.currentframe().f_code.co_name}: WB elastik (token1). {ex}')

            try:
                milvane = wb_milvane.combine_sales_remains()
            except Exception as ex:
                logging.error(f'{inspect.currentframe().f_code.co_name}: WB milvane (token2). {ex}')

            try:
                wb_spread.update_data(milvane, elastik)
            except Exception as ex:
                logging.error(f'{inspect.currentframe().f_code.co_name}: WB spread. {ex}')

            try:
                elastik, titles_elastic = ozon_elastik.combine_sales_remains()
            except Exception as ex:
                logging.error(f'{inspect.currentframe().f_code.co_name}: Ozon elastik (token1). {ex}')
            
            try:
                milvane, titles_milvane = ozon_milvane.combine_sales_remains()
            except Exception as ex:
                logging.error(f'{inspect.currentframe().f_code.co_name}: Ozon milvane (token2). {ex}')
            
            try:
                ozon_spread.update_data(milvane, elastik)
                ozon_spread.set_action_titles_milvane(titles_milvane)
                ozon_spread.set_action_titles_elastic(milvane, titles_elastic)
            except Exception as ex:
                logging.error(f'{inspect.currentframe().f_code.co_name}: Ozon spread. {ex}')
            time.sleep(settings.UPDATE_PERIOD * 86400 - 500)
        
        time.sleep(2)


if __name__ == '__main__':
    parse_data()