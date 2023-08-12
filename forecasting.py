import json
import logging
from concurrent.futures import ThreadPoolExecutor
import subprocess
from multiprocessing import Pool, Process, Queue, Manager
from multiprocessing.managers import SyncManager
import os
from datetime import datetime as dt


from external.client import YandexWeatherAPI
from tasks import (
    DataFetchingTask,
    DataCalculationTask,
    DataAggregationTask,
    DataAnalyzingTask,
)
from utils import CITIES, get_url_by_city_name

file_log = logging.FileHandler('Log.log')
console_out = logging.StreamHandler()

logging.basicConfig(handlers=(file_log, console_out),
                    format='[%(asctime)s | %(levelname)s]: %(message)s',
                    datefmt='%m.%d.%Y %H:%M:%S',
                    level=logging.INFO)


TMP_DIR = 'tmp'
RES_DIR = 'tmp/result'
CITIES_DATA = {}


def forecast_weather():
    """
    Анализ погодных условий по городам
    """

    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    queue = Queue()

    logging.info(f'Создали пул потоков для скачивания данных')
    with ThreadPoolExecutor() as pool:
        for city_name in CITIES:
            o_path = os.path.join(TMP_DIR, f"{city_name}.json")
            pool.submit(DataFetchingTask(queue).run, city_name, o_path)


    logging.info(f'Запускаем процессы для анализа данных')
    tasks = []
    calc_paths = Manager().dict()
    for _ in range(os.cpu_count()):
        task = DataCalculationTask(queue, calc_paths)
        task.start()
        tasks.append(task)

    for task in tasks:
        task.join()

    result = []
    with ThreadPoolExecutor() as pool:
        pool.map(DataAggregationTask(result).run, calc_paths.values())

    # Похоже распараллеливать данный шаг не имеет смысла
    DataAnalyzingTask().run(result, RES_DIR)


if __name__ == "__main__":
    forecast_weather()
