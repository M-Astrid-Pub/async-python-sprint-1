import logging
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Queue, Manager, Event
import os

from tasks import (
    DataFetchingTask,
    DataCalculationTask,
    DataAggregationTask,
    DataAnalyzingTask,
)
from utils import CITIES

file_log = logging.FileHandler("Log.log")
console_out = logging.StreamHandler()

logging.basicConfig(
    handlers=(file_log, console_out),
    format="[%(asctime)s | %(levelname)s]: %(message)s",
    datefmt="%m.%d.%Y %H:%M:%S",
    level=logging.INFO,
)


TMP_DIR = "tmp"
RES_DIR = "tmp/result"


def forecast_weather():
    """
    Анализ погодных условий по городам
    """

    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    queue = Queue()
    load_complete_event = Event()

    logging.info("Запускаем worker-процессы для рассчетов средних значений.")
    calc_tasks = []
    calc_paths = Manager().dict()
    for _ in range(os.cpu_count()):
        task = DataCalculationTask(queue, calc_paths, load_complete_event)
        task.start()
        calc_tasks.append(task)

    logging.info("Создали пул потоков  для скачивания данных.")
    with ThreadPoolExecutor() as pool:
        for city_name in CITIES:
            o_path = os.path.join(TMP_DIR, f"{city_name}.json")
            pool.submit(DataFetchingTask(queue).run, city_name, o_path)

    logging.info(
        "Закончили скачивание данных. Завершаем процессы рассчета средних."
    )
    load_complete_event.set()

    for task in calc_tasks:
        task.join()

    result = []
    logging.info("Запускаем пул потоков для аггрегации данных")
    with ThreadPoolExecutor() as pool:
        pool.map(DataAggregationTask(result).run, calc_paths.values())

    DataAnalyzingTask().run(result, RES_DIR)


if __name__ == "__main__":
    forecast_weather()
