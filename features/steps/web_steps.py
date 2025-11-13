from behave import given, then
from selenium.webdriver.common.by import By

@given("the browser opens the homepage")
def step_open_homepage(context):
    context.driver.get(context.base_url)

@then('the page should contain the text "{expected_text}"')
def step_check_json_text(context, expected_text):
    body_text = context.driver.find_element(By.TAG_NAME, "body").text
    assert expected_text in body_text, f"Expected '{expected_text}' in page, got '{body_text}'"
