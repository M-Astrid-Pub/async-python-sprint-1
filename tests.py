import json
import unittest
from multiprocessing import Queue, Event
import os
import shutil

import tasks

TEST_TMP_DIR = "tmp_tests"


class MyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(TEST_TMP_DIR):
            shutil.rmtree(TEST_TMP_DIR)
        os.makedirs(TEST_TMP_DIR)

        cls._create_test_city_data("TEST_CITY")
        cls.test_calc_paths = cls._create_test_city_calc_data()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(TEST_TMP_DIR)

    def test_data_fetch_task(self):
        queue = Queue()
        city_name = "MOSCOW"
        tasks.DataFetchingTask(queue, TEST_TMP_DIR).run(city_name)
        out_path = self._get_city_path(city_name)

        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r") as fd:
            data = json.load(fd)

        self.assertIsInstance(data, dict)
        self.assertGreater(len(data["forecasts"]), 0)
        self.assertFalse(queue.empty())
        self.assertEqual(queue.get(), ("MOSCOW", out_path))

    def test_calc_task(self):
        queue = Queue()
        break_event = Event()
        city_name = "TEST_CITY"
        queue.put(("TEST_CITY", self._get_city_path(city_name)))
        task = tasks.DataCalculationTask(queue, {}, break_event, TEST_TMP_DIR)
        task.start()

        break_event.set()

        task.join()

        out_path = f"{TEST_TMP_DIR}/{city_name}_calc.json"
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r") as fd:
            self.assertEqual(
                json.load(fd),
                {
                    "city_name": "TEST_CITY",
                    "mean_temperature": 11.727333333333334,
                    "mean_condition_hours": 9,
                },
            )

    def test_aggregate_task(self):
        res = []
        task = tasks.DataAggregationTask(res)

        for path in self.test_calc_paths:
            task.run(path)

        self.assertEqual(
            res,
            [
                {
                    "city_name": "TEST_CITY",
                    "mean_temperature": 11.727333333333334,
                    "mean_condition_hours": 9,
                },
                {
                    "city_name": "TEST_CITY1",
                    "mean_temperature": 12.727333333333334,
                    "mean_condition_hours": 10,
                },
            ],
        )

    def test_analyze_task(self):
        cities_data = [
            {
                "city_name": "TEST_CITY",
                "mean_temperature": 11.727333333333334,
                "mean_condition_hours": 9,
            },
            {
                "city_name": "TEST_CITY1",
                "mean_temperature": 12.727333333333334,
                "mean_condition_hours": 10,
            },
            {
                "city_name": "TEST_CITY3",
                "mean_temperature": 31.727333333333334,
                "mean_condition_hours": 1,
            },
            {
                "city_name": "TEST_CITY2",
                "mean_temperature": 31.727333333333334,
                "mean_condition_hours": 0,
            },
        ]
        res_dir = os.path.join(TEST_TMP_DIR, "results")
        task = tasks.DataAnalyzingTask()
        best_city = task.run(cities_data, res_dir)

        self.assertEqual(best_city, "TEST_CITY3")

    @staticmethod
    def _get_city_path(city_name: str):
        return os.path.join(TEST_TMP_DIR, f"{city_name}.json")

    @staticmethod
    def _create_test_city_data(city_name: str):
        shutil.copy(
            "examples/response.json",
            os.path.join(TEST_TMP_DIR, f"{city_name}.json"),
        )

    @staticmethod
    def _create_test_city_calc_data():
        test_calc_paths = []
        test_calc_paths.append(
            shutil.copy(
                "examples/output.json",
                os.path.join(TEST_TMP_DIR, "TEST_CALC_calc.json"),
            )
        )
        test_calc_paths.append(
            shutil.copy(
                "examples/output1.json",
                os.path.join(TEST_TMP_DIR, "TEST_CALC1_calc.json"),
            )
        )
        return test_calc_paths


if __name__ == "__main__":
    unittest.main()
