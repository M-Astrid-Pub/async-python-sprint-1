# Install



# Проектное задание первого спринта

Ваша задача — проанализировать данные по погодным условиям, полученные от API Яндекс Погоды.

## Описание задания

**1. Получите информацию о погодных условиях для указанного списка городов, используя API Яндекс Погоды.**

<details>
<summary> Описание </summary>

Список городов находится в переменной `CITIES` в файле [utils.py](utils.py). Для взаимодействия с API используйте готовый класс `YandexWeatherAPI` в модуле `external/client.py`. Пример работы с классом `YandexWeatherAPI` описан в <a href="#apiusingexample">примере</a>. Пример ответа от API для анализа вы найдёте в [файле](examples/response.json).

</details>

**2. Вычислите среднюю температуру и проанализируйте информацию об осадках за указанный период для всех городов.**

<details>
<summary> Описание </summary>

Условия и требования:
- период вычислений в течение дня — с 9 до 19 часов;
- средняя температура рассчитывается за указанный промежуток времени;
- сумма времени (часов), когда погода без осадков (без дождя, снега, града или грозы), рассчитывается за указанный промежуток времени;
- информация о температуре для указанного дня за определённый час находится по следующему пути: `forecasts> [день]> hours> temp`;
- информация об осадках для указанного дня за определённый час находится по следующему пути: `forecasts> [день]> hours> condition`.

[Пример данных](examples/response-day-info.png) с информацией о температуре и осадках за день.

Список вариантов погодных условий находится [в таблице в блоке `condition`](https://yandex.ru/dev/weather/doc/dg/concepts/forecast-test.html#resp-format__forecasts) или в [файле](examples/conditions.txt).

Для анализа данных используйте подготовленный скрипт в модуле `external/analyzer.py`. Скрипт имеет два параметра запуска:
- `-i` – путь до файла с данными, как результат ответа от `YandexWeatherAPI` в формате `json`;
- `-o` – путь до файла для сохранения результата выполнения работы.

Пример запуска скрипта:
```bash
python3 external/analyzer.py -i examples/response.json -o output.json
```

[Пример данных](examples/output.json) с информацией об анализе данных для одного города за период времени, указанный во входном файле.


</details>

**3. Объедините полученные данные и сохраните результат в текстовом файле.**

<details>
<summary> Описание </summary>

Формат сохраняемого файла – **json**, **yml**, **csv** или **xls/xlsx**.

Возможный формат таблицы для сохранения, где рейтинг — это позиция города относительно других при анализе «благоприятности поездки» (п.4).

| Город/день  |                           | 14-06 | ... | 19-06 | Среднее | Рейтинг |
|-------------|:--------------------------|:-----:|:---:|:-----:|--------:|--------:|
| Москва      | Температура, среднее      |  24   |     |  27   |    25.6 |       8 |
|             | Без осадков, часов        |   8   |     |   4   |       6 |         |
| Абу-Даби    | Температура, среднее      |  34   |     |  37   |    35.5 |       2 |
|             | Без осадков, часов        |   9   |     |  10   |     9.5 |         |
| ...         |                           |       |     |       |         |         |

</details>


**4. Проанализируйте результат и сделайте вывод, какой из городов наиболее благоприятен для поездки.**

<details>
<summary> Описание </summary>

Наиболее благоприятным городом считать тот, в котором средняя температура за всё время была самой высокой, а количество времени без осадков — максимальным.
Если таких городов более одного, то выводить все.

</details>

## Требования к решению

1. Используйте для решения как процессы, так и потоки. Для этого разделите все задачи по их типу – IO-bound или CPU-bound.
2. Используйте для решения и очередь, и пул задач.
3. Опишите этапы решения в виде отдельных классов в модуле [tasks.py](tasks.py):
  - `DataFetchingTask` — получение данных через API;
  - `DataCalculationTask` — вычисление погодных параметров;
  - `DataAggregationTask` — объединение вычисленных данных;
  - `DataAnalyzingTask` — финальный анализ и получение результата.
4. Используйте концепции ООП.
5. Предусмотрите обработку исключительных ситуаций.
6. Логируйте результаты действий.
7. Используйте аннотацию типов.
8. Приведите стиль кода в соответствие pep8, flake8, mypy.


## Рекомендации к решению

1. Предусмотрите и обработайте ситуации с некорректным обращением к внешнему API: отсутствующая/битая ссылка, неверный ответ, невалидное содержимое или иной формат ответа.  
2. Покройте написанный код тестами.
3. Используйте таймауты для ограничения времени выполнения частей программы и принудительного завершения при зависаниях или нештатных ситуациях.


---

<a name="apiusingexample"></a>

## Пример использования `YandexWeatherAPI` для работы с API

```python
from external.client import YandexWeatherAPI
from utils import get_url_by_city_name

city_name = "MOSCOW"
url_with_data = get_url_by_city_name(city_name)
resp = YandexWeatherAPI.get_forecasting(data_url)
```
