import os
import requests
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

@given(u'the application is started')
def step_impl(context):
    context.base_url = os.getenv('BASE_URL','http://localhost:8080')
    context.resp = requests.get(context.base_url + '/')
    assert context.resp.status_code == 200


@when(u'I visit the "Home Page"')
def step_impl(context):
    context.resp = requests.get(context.base_url + '/')
    assert context.resp.status_code == 200


@then(u'I should see "{message}" in the title')
def step_impl(context, message):
    resp = requests.get(context.base_url) 
    resp.raise_for_status()  
    data = resp.json()       

    # Check that the "service" field matches expected value
    assert data.get("service") == "Product REST API Service", f"Expected 'Product REST API Service', got '{data.get('service')}'"


@then(u'I should not see "{message}"')
def step_impl(context, message):
    assert message not in str(context.resp.text)