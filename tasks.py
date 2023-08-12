import json
import logging
import os
import traceback
from multiprocessing import Queue, Process, Event
from queue import Empty
from typing import List, Dict
from statistics import mean
from datetime import datetime as dt
import time

from external import analyzer
from external.client import YandexWeatherAPI
from utils import get_url_by_city_name


def log_exc(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception:
            logging.error(traceback.print_exc())

    return wrapper


class DataFetchingTask:

    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    @log_exc
    def run(self, city_name: str, out_path: str):
        logging.info(f'Получаем данные для {city_name}')
        url_with_data = get_url_by_city_name(city_name)
        res = YandexWeatherAPI.get_forecasting(url_with_data)
        with open(out_path, 'w') as fd:
            json.dump(res, fd)
        logging.info(f'Успешно выгрузили данные для {city_name} в {out_path}')

        self.queue.put((city_name, out_path))
        logging.info(f'Добавили в очередь обработки {city_name}')


class DataCalculationTask(Process):
    def __init__(self, q: Queue, l: Dict, e: Event):
        super().__init__()
        self.queue = q
        self.paths = l
        self.break_event = e

    @log_exc
    def run(self):
        while True:
            if self.queue.empty() and self.break_event.is_set():
                logging.info(f'Все задания обработаны. Завершаем {self.name}.')
                break
            else:
                try:
                    (city_name, path) = self.queue.get(block=False)
                except Empty:
                    continue
                self.analyze(city_name, path)

    def analyze(self, city_name: str, path: str):
        logging.info(f'Считаем средние для {path} в {self.name}')

        data = analyzer.load_data(path)
        data = analyzer.analyze_json(data)
        mean_tmp, mean_cond = self._count_means(data)
        data = {'city_name': city_name, 'mean_temperature': mean_tmp, 'mean_condition_hours': mean_cond}

        out_path = f"tmp/{city_name}_calc.json"
        with open(out_path, 'w') as fd:
            json.dump(data, fd)

        self.paths[city_name] = out_path
        logging.info(f'Успешно посчитали средние для {path} в {self.name}')

    @staticmethod
    def _count_means(data: Dict):
        temps, conds = [], []
        for day in data["days"]:
            if day["temp_avg"] is None:
                continue
            temps.append(day["temp_avg"])
            conds.append(day["relevant_cond_hours"])
        if not len(temps):
            raise Exception('No temp data')
        return mean(temps), mean(conds)


class DataAggregationTask:

    def __init__(self, res: List):
        super().__init__()
        self.res = res

    @log_exc
    def run(self, path: str):
        logging.info(f'Выбираем данные из {path}')
        data = analyzer.load_data(path)
        self.res.append(data)


class DataAnalyzingTask:

    @log_exc
    def run(self, data, res_dir):
        logging.info(f'Сортируем данные для получения рейтинга.')
        logging.debug(data)
        self._sort_data(data)

        logging.info(f'Присваиваем рейтинг городам')
        for rating, city_data in enumerate(data):
            city_data["rating"] = rating + 1

        best_city = data[0]["city_name"]
        print(f"Наиболее благоприятный город: {best_city}.")

        if not os.path.exists(res_dir):
            os.makedirs(res_dir)
        res_path = os.path.join(res_dir, f'{dt.now().strftime("%Y.%m.%d.%H%M%S")}.json')
        with open(res_path, 'w') as fd:
            json.dump(data, fd)
        print(f"Полный результат сохранен в {res_path}")

    @staticmethod
    def _sort_data(data):
        data.sort(key=lambda x: x['mean_condition_hours'])
        data.sort(key=lambda x: x['mean_temperature'] * -1)
