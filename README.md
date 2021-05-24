# Геокодер

Авторы: Данил Казаков, Александр Мошков ФТ-102

## Описание

Приложение позволяет получить координаты здания по адресу (прямой геокодинг или просто геокодинг) и адрес здания по координатам (обратный геокодинг).

Работает для всех городов России (пока что только для городов с населением больше 100 тыс. человек).

## Установка зависимостей
```pip install -r requirements.txt```

## Аргументы командной строки

- ```-g, --geocoder``` - используется для [прямого] геокодинга, принимает 3 параметра: ```city```, ```street```, ```house_number```.

- ```-r, --reverse``` - используется для обратного геокодинга, принимает 2 параметра ```latitude```, ```longitude```.

- ```-a, --additional``` - вывод дополнительной информации о здании(той, что на OSM).

- ```-o, --organizations``` - вывод всех организаций в здании.

- ```-j, --json``` - вывод результатов в файл ```.json```, в файле также будет дополнительная информация и информация об организациях.

## Примеры запуска

```python main.py -g Ижевск Горького 68 -j``` 
- выведет информацию о здании, находящемся по адресу ```Ижевск, ул. Максима Горького, 68``` в файл ```.json```.

```python main.py -r 56.84477 53.20044 -a```
- выведет информацию(вместе с дополнительной) о здании, находящемуся по координатам ```56.84477, 53.20044```.


Слово ```улица, проспект, и т.д``` указывать необязательно, но может возникнуть ситуация, когда существует 2 и более улиц с похожими названиями, например: ```Морская улица``` и ```Морская набережная```, в таком случае нужно будет указать именно то, что вы имеете ввиду.

__Если название улицы состоит более чем из одного слова, вы можете записать его в кавычках: ```"40 лет Победы"```, либо же, без кавычек, но и без пробелов: ```40летпобеды```.__

## Состав

- ```main.py``` - основной модуль для взаимодействия с программой.
- ```xml_parser.py``` - модуль для преобразования ```.xml(.osm)``` файлов в базу данных ```.db```.
- ```geocoder.py``` - модуль для прямого геокодинга.
- ```reverse_geocoder.py``` - модуль для обратного геокодинга.
- ```organizations.py``` - модуль для нахождения организаций в здании.
- ```downloader.py``` - модуль для скачивания ```.xml``` файла нужного города с сервера OSM.
- ```printer.py``` - модуль для вывода результатов работы программы на консоль или в ```.json``` файл.
- ```extensions.py``` - модуль содержит методы, которые не были размещены в других модулях.
- ```db/cities.db``` - база данных, которая содержит информацию о городах, а именно название и пограничную рамку(крайние координаты).

После запуска программы создастся две директории: ```xml``` и ```json```, в них будут храниться соответствующие файлы.

## Тесты

- ```tests.py``` - модуль с unit-тестами.

Используется библиотека ```pytest```, на данный момент покрытие по строкам составляет ~60%.

## Подробности реализации

При запуске программа сначала проверяет не существует ли база данных введённого города (либо база данных города, которому принадлежат введённые координаты), если существует, то начинает работать с ней, иначе проверяет наличие ```.xml``` файла нужного города, если он есть, то программа преобразует его в базу данных, а если нет, то скачивает с сервера OSM файл и преобразует его.

В базе данных каждого города существует две таблицы: ```nodes``` с полями 
- ```id```
- ```lat```
- ```lon```
- все теги (которые нашлись в ```.xml```)

и ```ways``` (сюда так же входят ```relation```, которые являются зданиями) с полями 
- ```id```
- ```nodes``` (которые входят в состав) 
- ```lat```
- ```lon``` (некая внутренняя точка) 
- все теги (которые нашлись в ```.xml```).

Поиск по базе осуществляется средствами ```SQLite3```.
