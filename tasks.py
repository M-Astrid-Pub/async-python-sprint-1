import json
import logging
import os
import traceback
from multiprocessing import Queue, Process
from multiprocessing.synchronize import Event
from queue import Empty
from typing import List, Dict
from statistics import mean
from datetime import datetime as dt
from urllib.error import HTTPError

from exceptions import InvalidDataError, InvalidWeatherData
from external import analyzer
from external.client import YandexWeatherAPI
from external.resp_model import AnalyzedApiRespModel
from utils import get_url_by_city_name


def log_exc(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception:
            logging.error(traceback.print_exc())
            raise

    return wrapper


class DataFetchingTask:
    def __init__(self, queue: Queue, out_dir: str):
        super().__init__()
        self.queue = queue
        self.out_dir = out_dir

    def _load_data(self, city_name: str):
        url_with_data = get_url_by_city_name(city_name)
        try:
            res = YandexWeatherAPI.get_forecasting(url_with_data)
        except HTTPError:
            logging.exception(
                f"Не удалось получить информацию по {city_name}.",
                f"URL: {url_with_data}",
            )
            raise

        out_path = os.path.join(self.out_dir, f"{city_name}.json")
        with open(out_path, "w") as fd:
            json.dump(res, fd)

        return out_path

    @log_exc
    def run(self, city_name: str):
        logging.info(f"Получаем данные для {city_name}")
        out_path = self._load_data(city_name)
        logging.info(f"Успешно выгрузили данные для {city_name} в {out_path}")

        self.queue.put((city_name, out_path))
        logging.info(f"Добавили в очередь обработки {city_name}")


class DataCalculationTask(Process):
    def __init__(self, queue: Queue, paths: Dict, event: Event, dir: "str"):
        super().__init__()
        self.queue = queue
        self.paths = paths
        self.break_event = event
        self.dir = dir

    @log_exc
    def run(self):
        while True:
            if self.queue.empty() and self.break_event.is_set():
                logging.info(f"Все задания обработаны. Завершаем {self.name}.")
                break
            else:
                try:
                    (city_name, path) = self.queue.get(block=False)
                except Empty:
                    continue
                self.analyze(city_name, path)

    def analyze(self, city_name: str, path: str):
        logging.info(f"Считаем средние для {path} в {self.name}")

        data = analyzer.load_data(path)
        data = analyzer.analyze_json(data)
        try:
            data = AnalyzedApiRespModel.from_dict(data)
        except KeyError as e:
            raise InvalidDataError(
                f"Структура {path} невалидна. Отсутствует ключ {e}.",
                "Пропускаем город.",
            ) from e

        mean_tmp, mean_cond = self._count_means(data)
        data = {
            "city_name": city_name,
            "mean_temperature": mean_tmp,
            "mean_condition_hours": mean_cond,
        }

        out_path = f"{self.dir}/{city_name}_calc.json"
        with open(out_path, "w") as fd:
            json.dump(data, fd)

        self.paths[city_name] = out_path
        logging.info(f"Успешно посчитали средние для {path} в {self.name}")

    @staticmethod
    def _count_means(data: AnalyzedApiRespModel):
        temps, conds = [], []
        for day in data.days:
            if day.temp_avg is None:
                continue
            temps.append(day.temp_avg)
            conds.append(day.relevant_cond_hours)
        if not len(temps):
            raise InvalidWeatherData("No average temperature data")
        return mean(temps), mean(conds)


class DataAggregationTask:
    def __init__(self, res: List):
        super().__init__()
        self.res = res

    @log_exc
    def run(self, path: str):
        logging.info(f"Выбираем данные из {path}")
        data = analyzer.load_data(path)
        self.res.append(data)


class DataAnalyzingTask:
    @staticmethod
    def run(data: List, res_dir: str):
        logging.info("Сортируем данные для получения рейтинга.")
        logging.debug(data)

        data.sort(
            key=lambda x: (
                x["mean_temperature"],
                x["mean_condition_hours"],
            ),
            reverse=True,
        )

        logging.info("Присваиваем рейтинг городам")
        for rating, city_data in enumerate(data):
            city_data["rating"] = rating + 1

        best_city = data[0]["city_name"]
        print(f"Наиболее благоприятный город: {best_city}.")

        if not os.path.exists(res_dir):
            os.makedirs(res_dir)
        res_path = os.path.join(
            res_dir, f'{dt.now().strftime("%Y.%m.%d.%H%M%S")}.json'
        )
        with open(res_path, "w") as fd:
            json.dump(data, fd)
        print(f"Полный результат сохранен в {res_path}")

        return best_city
