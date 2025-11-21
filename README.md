# lavash-ui-tests

Автотесты для веб-приложения «#Лаваш».

В проекте находятся мои тесты, написанные для диплома.  
Использовал Python, Pytest, Selenium и Allure.

### Что есть в репозитории:
- test_lavash_smoke.py — смоук-набор из 10 тестов  
- conftest.py — фикстуры для браузера  
- README.md  
- requirements.txt (если нужно — можно удалить)

Как запускать тесты:
Запуск всех тестов:
pytest test_lavash_smoke.py -v
Запуск с генерацией отчёта Allure:
pytest test_lavash_smoke.py -v –alluredir=allure-results
Создать и открыть отчёт:
allure generate allure-results –clean -o allure-report
allure open allure-report
Используемые технологии:
- Python  
- Selenium WebDriver  
- Pytest  
- Allure Report  
- ChromeDriver  

Автор: Бубенко Анатолий Игоревич  
Работа выполнена для диплома по тестированию.
