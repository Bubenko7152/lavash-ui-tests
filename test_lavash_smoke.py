import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://mylavash.ru/omsk"


# ---------- FIXTURE С ДРАЙВЕРОМ ----------

@pytest.fixture(scope="session")
def driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    drv = webdriver.Chrome(options=options)
    drv.maximize_window()
    yield drv
    drv.quit()


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------

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


def ensure_address_selected(driver):
    """
    Для доставки: если появилась большая карта — вводим 'Мира 10'
    и закрываем модалку.
    """
    wait = WebDriverWait(driver, 20)
    wait_short = WebDriverWait(driver, 3)

    try:
        addr_input = wait_short.until(
            EC.visibility_of_element_located((By.ID, "suggest"))
        )
    except TimeoutException:
        return

    addr_input.click()
    addr_input.clear()
    addr_input.send_keys("Мира 10")

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
        pass

    try:
        choose_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class,'modal-address__button')]//button")
            )
        )
        driver.execute_script("arguments[0].click();", choose_btn)
    except TimeoutException:
        try:
            choose_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space()='Выбрать']")
                )
            )
            driver.execute_script("arguments[0].click();", choose_btn)
        except TimeoutException:
            pass

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


def open_main(driver):
    """Открыть сайт, выбрать адрес доставки и закрыть баннеры."""
    driver.get(BASE_URL)
    ensure_address_selected(driver)
    close_cookie_banner_if_needed(driver)


def open_main_without_address(driver):
    """
    Открыть сайт, НИЧЕГО не выбирать (адрес не задаём),
    только закрыть баннер с куками.
    Используется для теста бага самовывоза.
    """
    driver.get(BASE_URL)
    close_cookie_banner_if_needed(driver)


def click_category(driver, name: str):
    """Клик по кнопке категории."""
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

    card = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.product-card, li.product-card")
        )
    )

    add_btn = card.find_element(
        By.CSS_SELECTOR,
        "button[aria-label='add-product'], "
        "button.btn.product-card__btn, "
        "button.btn"
    )
    driver.execute_script("arguments[0].click();", add_btn)

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
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "div.modal-product-details, div.modal_product, div.modal-product"
                )
            )
        )
    except TimeoutException:
        pass


def cart_has_products(driver) -> bool:
    """Проверяем, что в корзине есть хотя бы один товар."""
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
        return

    try:
        confirm_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@class,'modal-confirm__button') "
                    "and contains(.,'Подтвердить')]"
                )
            )
        )
        driver.execute_script("arguments[0].click();", confirm_btn)
    except TimeoutException:
        try:
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


def open_pickup_points_list(driver):
    """
    Открывает вкладку 'Самовывоз' и нажимает 'Посмотреть список точек'
    на большой карте. Используем только когда адрес ещё НЕ выбран.
    """
    wait = WebDriverWait(driver, 20)

    pickup_tab = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Самовывоз']")
        )
    )
    pickup_tab.click()

    show_list_btn = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.modal-address__show-list-button")
        )
    )
    show_list_btn.click()


# ------------------------------------------------------------
#   🔥 ТЕСТ БАГА — ДОЛЖЕН ИДТИ ПЕРВЫМ В ФАЙЛЕ
# ------------------------------------------------------------

@pytest.mark.smoke
def test_00_pickup_search_address_without_comma_bug(driver):
    open_main_without_address(driver)
    wait = WebDriverWait(driver, 20)

    # 1. Переключить в режим Самовывоза
    pickup_checkbox = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "input.btn-switch__checkbox")
    )
    )
    driver.execute_script("arguments[0].click();", pickup_checkbox)

    wait.until(
    EC.text_to_be_present_in_element(
        (By.CSS_SELECTOR, "label.btn-switch__label"), "Самовывоз"
    )
    )

    # --- 2. Нажать "Посмотреть список точек" ---
    show_list_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class,'modal-address__show-list-button') "
                "   or contains(., 'Посмотреть список точек')]")
        )
    )
    driver.execute_script("arguments[0].click();", show_list_btn)

    # 2. Найти поле поиска
    search_input = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.modal-address__search div.input-search input[type='text']")
        )
    )

    # гарантируем фокус
    driver.execute_script("arguments[0].focus();", search_input)

 pytest test_lavash_smoke.py -k "pickup_search_address" -v
    search_input.send_keys("мира 29")
    search_input.send_keys(Keys.ENTER)

    # 3. Проверить список точек
    cards = driver.find_elements(
        By.CSS_SELECTOR,
        "div.modal-address__cards div.modal-address__card"
    )

    assert len(cards) > 0, "БАГ: при вводе 'мира 29' список точек самовывоза пуст!"


# ------------------------------------------------------------
#                    СМОУК-ТЕСТЫ (остальные)
# ------------------------------------------------------------

@pytest.mark.smoke
def test_01_set_address_mira_10(driver):
    """TC-01: Можно открыть сайт и задать адрес 'Мира 10'."""
    open_main(driver)
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
    """TC-06: Можно добавить 'Картофель фри' в корзину."""
    open_main(driver)
    click_category(driver, "Закуски")
    clear_cart_if_possible(driver)
    add_first_product_in_list(driver)
    assert cart_has_products(driver)


@pytest.mark.smoke
def test_07_add_sauce_to_cart(driver):
    """TC-07: Можно добавить соус в корзину."""
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

    empty_text = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Корзина пуста')]")
        )
    )
    assert "Корзина пуста" in empty_text.text


@pytest.mark.smoke
def test_10_cart_persists_after_category_change(driver):
    """
    TC-10: Товар остаётся в корзине после смены категории.
    """
    open_main(driver)
    click_category(driver, "Соусы")
    clear_cart_if_possible(driver)
    add_first_product_in_list(driver)
    assert cart_has_products(driver)

    click_category(driver, "Закуски")
    assert cart_has_products(driver)

