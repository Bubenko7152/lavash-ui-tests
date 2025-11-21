import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://mylavash.ru/omsk"


# ---------- FIXTURE С ДРАЙВЕРОМ (ОДИН НА ВСЕ ТЕСТЫ) ----------

@pytest.fixture(scope="session")
def driver():
    options = webdriver.ChromeOptions()
    # если нужно без головы, раскомментируй:
    # options.add_argument("--headless=new")

    drv = webdriver.Chrome(options=options)
    drv.maximize_window()
    yield drv
    drv.quit()


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ В ЭТОМ ЖЕ ФАЙЛЕ ----------

def ensure_address_selected(driver):
    """
    Если всплыла большая карта с выбором адреса — вводим 'Мира, 10',
    выбираем первый вариант из подсказок и нажимаем 'Выбрать'.
    Если модалки нет — тихо выходим.
    """
    wait = WebDriverWait(driver, 20)
    wait_short = WebDriverWait(driver, 3)

    # 1. Пытаемся найти инпут с адресом (id='suggest')
    try:
        addr_input = wait_short.until(
            EC.visibility_of_element_located((By.ID, "suggest"))
        )
    except TimeoutException:
        # Модалки нет
        return

    # 2. Вводим адрес
    addr_input.click()
    addr_input.clear()
    addr_input.send_keys("Мира, 10")

    # 3. Ждём подсказки и кликаем по первой
    try:
        first_suggest = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    ".suggest-addresses li, .suggest-addresses__item"
                )
            )
        )
        first_suggest.click()
    except TimeoutException:
        # Если подсказки не появились – идём дальше как есть
        pass

    # 4. Ждём, пока станет активна кнопка "Выбрать", и жмём её
    try:
        choose_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class,'modal-address__button')]//button"
                )
            )
        )
        driver.execute_script("arguments[0].click();", choose_btn)
    except TimeoutException:
        # На всякий случай пробуем кнопку по тексту
        try:
            choose_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space()='Выбрать']")
                )
            )
            driver.execute_script("arguments[0].click();", choose_btn)
        except TimeoutException:
            pass

    # 5. Ждём исчезновения модалки с картой (как у тебя было)
    try:
        wait.until(
            EC.invisibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "div.modal-address, div.address-autocomplete, div[id='modals']",
                )
            )
        )
    except TimeoutException:
        pass


def close_cookie_banner_if_needed(driver):
    """Закрываем баннер 'Принять!' если мешает."""
    try:
        btn = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Принять')]")
            )
        )
        driver.execute_script("arguments[0].click();", btn)
    except TimeoutException:
        pass


def open_main(driver):
    """Открыть главную, задать адрес и убрать баннеры."""
    driver.get(BASE_URL)
    ensure_address_selected(driver)
    close_cookie_banner_if_needed(driver)


def click_category(driver, name: str):
    """Клик по кнопке категории (Шаверма, Комбо, Соусы, Закуски и т.п.)."""
    wait = WebDriverWait(driver, 15)
    btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//button[normalize-space()='{name}']")
        )
    )
    driver.execute_script("arguments[0].click();", btn)


def add_first_product_in_list(driver):
    """
    Нажимаем 'Добавить' у первого товара в текущей категории.
    Если открылась модалка с деталями — жмём там 'Добавить'.
    """
    wait = WebDriverWait(driver, 15)

    # Ищем первую карточку товара
    card = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.product-card, li.product-card")
        )
    )

    # Кнопка "Добавить" внутри карточки
    add_btn = card.find_element(
        By.CSS_SELECTOR,
        "button[aria-label='add-product'], "
        "button.btn.product-card__btn, "
        "button.btn"
    )
    driver.execute_script("arguments[0].click();", add_btn)

    # Если всплыла модалка "С этим товаром выбирают" / детали товара — подтверждаем
    try:
        modal_add_btn = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button.modal-product-details__add-to-cart, "
                    "div.modal-product-details__controls button.btn-big, "
                    "div.modal_footer button.btn-big.btn-color"
                )
            )
        )
        driver.execute_script("arguments[0].click();", modal_add_btn)
        # Ждём исчезновения модалки
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "div.modal-product-details, div.modal_product, div.modal-product"
                )
            )
        )
    except TimeoutException:
        # Модалки нет — товар сразу добавился
        pass


def cart_has_products(driver) -> bool:
    """Проверяем, что в корзине есть хотя бы один товар (любой формат)."""
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//li[contains(@class,'cart-product') or "
                    "contains(@class,'cart__product')]"
                    "|//div[contains(@class,'cart-product')]"
                )
            )
        )
        return True
    except TimeoutException:
        return False


def clear_cart_if_possible(driver):
    """
    Нажимаем 'Очистить корзину', если ссылка видна.
    Если появляется модалка 'Вы уверены?' — жмём 'Подтвердить'.
    """
    wait = WebDriverWait(driver, 10)

    try:
        clear_link = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(., 'Очистить корзину')] | "
                    "//a[contains(., 'Очистить корзину')]",
                )
            )
        )
        driver.execute_script("arguments[0].click();", clear_link)
    except TimeoutException:
        return  # Нечего чистить

    # модалка подтверждения
    try:
        confirm_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@class,'modal-confirm__button') "
                    "and (contains(.,'Подтвердить') or contains(.,'Подтвердить'))]"
                )
            )
        )
        driver.execute_script("arguments[0].click();", confirm_btn)
    except TimeoutException:
        try:
            # запасной селектор
            confirm_btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button.modal-confirm__button, "
                        "div.modal-confirm__buttons button.btn-color"
                    )
                )
            )
            driver.execute_script("arguments[0].click();", confirm_btn)
        except TimeoutException:
            pass


# ------------------------------------------------------------
#                    СМОУК-ТЕСТЫ (10 штук)
# ------------------------------------------------------------

@pytest.mark.smoke
def test_01_set_address_mira_10(driver):
    """TC-01: Можно открыть сайт и задать адрес 'Мира 10'."""
    open_main(driver)

    # Проверяем, что карта закрылась и виден текст 'Ваш заказ'
    h2 = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//h2[normalize-space()='Ваш заказ']")
        )
    )
    assert "Ваш заказ" in h2.text


@pytest.mark.smoke
def test_02_navigation_buttons_exist(driver):
    """TC-02: На главной есть основные кнопки категорий."""
    open_main(driver)

    # на сайте именно "Шаверма", не "Шаурма"
    categories = ["Шаверма", "Комбо", "Соусы", "Закуски"]
    for cat in categories:
        elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//button[normalize-space()='{cat}']")
            )
        )
        assert elem.is_displayed()


@pytest.mark.smoke
def test_03_cart_is_empty_initially(driver):
    """TC-03: При заходе корзина пустая (есть текст 'Корзина пуста')."""
    open_main(driver)

    empty_text = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Корзина пуста')]")
        )
    )
    assert "Корзина пуста" in empty_text.text


@pytest.mark.smoke
def test_04_open_shawarma_category(driver):
    """TC-04: Можно открыть категорию 'Шаверма' и увидеть товары."""
    open_main(driver)
    click_category(driver, "Шаверма")

    # Ожидаем, что хотя бы одна карточка шаурмы появилась
    card = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.product-card, li.product-card")
        )
    )
    assert card.is_displayed()


@pytest.mark.smoke
def test_05_open_sauces_category(driver):
    """TC-05: Можно открыть категорию 'Соусы' и увидеть товары."""
    open_main(driver)
    click_category(driver, "Соусы")

    card = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.product-card, li.product-card")
        )
    )
    assert card.is_displayed()


@pytest.mark.smoke
def test_06_add_fries_to_cart(driver):
    """TC-06: Можно добавить 'Картофель фри' (первый товар в 'Закуски') в корзину."""
    open_main(driver)
    click_category(driver, "Закуски")

    # очищаем корзину перед проверкой
    clear_cart_if_possible(driver)

    add_first_product_in_list(driver)

    assert cart_has_products(driver)


@pytest.mark.smoke
def test_07_add_sauce_to_cart(driver):
    """TC-07: Можно добавить соус (первый товар в 'Соусы') в корзину."""
    open_main(driver)
    click_category(driver, "Соусы")
    clear_cart_if_possible(driver)

    add_first_product_in_list(driver)

    assert cart_has_products(driver)


@pytest.mark.smoke
def test_08_cart_product_has_title(driver):
    """TC-08: У товара в корзине есть заголовок."""
    open_main(driver)
    click_category(driver, "Соусы")
    clear_cart_if_possible(driver)

    add_first_product_in_list(driver)

    title = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                ".cart-product__title, "
                "li.cart-product h4, "
                "li.cart-product .title"
            )
        )
    )
    assert title.text.strip() != ""


@pytest.mark.smoke
def test_09_clear_cart_button_works(driver):
    """TC-09: Кнопка 'Очистить корзину' очищает корзину."""
    open_main(driver)
    click_category(driver, "Соусы")
    add_first_product_in_list(driver)

    assert cart_has_products(driver)

    clear_cart_if_possible(driver)

    # После очистки снова должен появиться текст 'Корзина пуста'
    empty_text = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Корзина пуста')]")
        )
    )
    assert "Корзина пуста" in empty_text.text


@pytest.mark.smoke
def test_10_cart_persists_after_category_change(driver):
    """
    TC-10: Товар остаётся в корзине после смены категории
    (добавили из 'Соусы', перешли в 'Закуски', корзина не пустая).
    """
    open_main(driver)
    click_category(driver, "Соусы")
    clear_cart_if_possible(driver)

    add_first_product_in_list(driver)
    assert cart_has_products(driver)

    # меняем категорию
    click_category(driver, "Закуски")

    # корзина всё ещё не пустая
    assert cart_has_products(driver)
