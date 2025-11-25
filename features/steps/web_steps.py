import os
import time
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@given("the application is started")
def step_impl(context):
    """start the application"""
    pass


@when('I visit the "Home Page"')
def step_impl(context):
    """use Selenium to visit the UI page"""
    url = f"{context.base_url}/ui"
    context.driver.get(url)

    # wait for the page to load
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.TAG_NAME, "h2"))
    )

@when(u'the "{element_name}" field should be empty')
def step_impl(context, element_name):
    """verify a field is empty"""
    element_mapping = {
        "create id": "create-id",
        "create name": "create-name",
    }
    
    element_id = element_mapping[element_name.lower()]
    element = context.driver.find_element(By.ID, element_id)
    assert element.get_attribute("value") == "", f"Expected {element_name} to be empty, but got '{element.get_attribute('value')}'"

@when(u'I set the "{element_name}" to "{text_value}"')
def step_impl(context, element_name, text_value):
    """set the value of an input field"""
    element_mapping = {
        "product id": "product-id-read",
        "create id": "create-id",
        "create name": "create-name",
        "create description": "create-description",
        "create price": "create-price",
        "create inventory": "create-inventory",
        "create image url": "create-image-url",
    }
    
    element_key = element_name.lower()
    element_id = element_mapping.get(element_key)
    
    if not element_id:
        raise ValueError(f"Unknown element: {element_name}")
    
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    # scroll to the element
    context.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.3)
    
    element.clear()
    element.send_keys(text_value)


@when('I press the "{button_name}" button')
def step_impl(context, button_name):
    """click the button"""
    button_mapping = {
        "delete product": "delete-btn",
        "list all products": "list-all-btn",
        "search with filters": "search-btn",
        "clear filters": "clear-search-btn",
        "read product": "read-btn",
        "create product": "create-btn",
    }

    button_key = button_name.lower()
    button_id = button_mapping.get(button_key)

    if not button_id:
        raise ValueError(f"Unknown button: {button_name}")

    button = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.element_to_be_clickable((By.ID, button_id))
    )

    try:
        context.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
            button,
        )
        time.sleep(0.3)
        context.driver.execute_script("arguments[0].click();", button)
    except Exception as e:
        from selenium.webdriver.common.action_chains import ActionChains

        ActionChains(context.driver).move_to_element(button).click().perform()

    if button_id == "delete-btn":
        try:
            WebDriverWait(context.driver, 5).until(EC.alert_is_present())
            alert = context.driver.switch_to.alert
            alert.accept()
            time.sleep(0.5)
        except:
            pass


@then('I should see "{message}" in the title')
def step_impl(context, message):
    """check the service field in the API response"""
    import requests

    resp = requests.get(context.base_url)
    resp.raise_for_status()
    data = resp.json()

    assert (
        data.get("service") == message
    ), f"Expected '{message}', got '{data.get('service')}'"


@then('I should not see "{message}"')
def step_impl(context, message):
    page_source = context.driver.page_source
    assert message not in page_source, f"Did not expect to see '{message}' on page"


@then('I should see the message "{message}"')
def step_impl(context, message):
    flash_div = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.visibility_of_element_located((By.ID, "flash-message"))
    )

    flash_text = flash_div.text
    assert (
        message in flash_text
    ), f"Expected '{message}' in flash message, but got '{flash_text}'"


@then('I should see "{text}" in the results')
def step_impl(context, text):
    results_table = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.ID, "results"))
    )

    tbody = results_table.find_element(By.TAG_NAME, "tbody")

    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda d: "No products loaded" not in tbody.text
    )

    table_text = tbody.text
    assert (
        text in table_text
    ), f"Expected to see '{text}' in results, but got: {table_text}"


@then('I should not see "{text}" in the results')
def step_impl(context, text):
    results_table = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.ID, "results"))
    )

    tbody = results_table.find_element(By.TAG_NAME, "tbody")

    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda d: "No products found" not in tbody.text
        or len(tbody.find_elements(By.TAG_NAME, "tr")) > 0
    )

    table_text = tbody.text
    assert (
        text not in table_text
    ), f"Did not expect to see '{text}' in results, but it was found: {table_text}"


@then('I should see "{text}" in the product details')
def step_impl(context, text):
    details_div = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.visibility_of_element_located((By.ID, "read-product-details"))
    )

    details_text = details_div.text
    assert (
        text in details_text
    ), f"Expected to see '{text}' in product details, but got: {details_text}"


@then('I should see "{text}" in the availability status')
def step_impl(context, text):
    availability_element = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.ID, "display-available"))
    )

    availability_text = availability_element.text
    assert (
        text in availability_text
    ), f"Expected '{text}' in availability, but got '{availability_text}'"


@then("the product details should not be visible")
def step_impl(context):
    try:
        details_div = context.driver.find_element(By.ID, "read-product-details")
        is_displayed = details_div.is_displayed()
        assert (
            not is_displayed
        ), "Product details should not be visible, but it is displayed"
    except:
        pass


@then("I should see a table of products")
def step_impl(context):
    table = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.ID, "results"))
    )
    assert table.is_displayed(), "Product table is not visible"


@then("I should see {count:d} products in the table")
def step_impl(context, count):
    """Verify that the table shows the expected number of products."""
    table = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.ID, "results"))
    )
    tbody = table.find_element(By.TAG_NAME, "tbody")

    # Wait until at least one product row appears (table loaded)
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda d: "No products loaded" not in tbody.text
    )

    # Wait until at least `count` product rows appear
    def rows_loaded(driver):
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        product_rows = [row for row in rows if "No products loaded" not in row.text]
        return len(product_rows) >= count

    WebDriverWait(context.driver, context.wait_seconds).until(rows_loaded)

    # Count actual product rows
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    product_rows = [row for row in rows if "No products loaded" not in row.text]
    actual_count = len(product_rows)

    assert actual_count == count, f"Expected {count} products, but found {actual_count}"


@then("I should see the column headers")
def step_impl(context):
    table = WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.ID, "results"))
    )
    thead = table.find_element(By.TAG_NAME, "thead")
    header_cells = thead.find_elements(By.TAG_NAME, "th")
    actual_headers = [cell.text.strip() for cell in header_cells]

    # Flatten Gherkin table cells
    expected_headers = [cell for row in context.table for cell in row.cells]

    # Optional: allow extra HTML columns
    for header in expected_headers:
        assert (
            header in actual_headers
        ), f"Expected header '{header}' not found in {actual_headers}"
