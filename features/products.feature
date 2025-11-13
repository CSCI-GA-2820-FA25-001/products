Feature: Test BDD environment

  Scenario: Homepage loads JSON
    Given the browser opens the homepage
    Then the page should contain the text "Product REST API Service"

# Feature: Manage Products via the Admin UI
#   As an eCommerce manager
#   I want to manage products through the web interface
#   So that I can create, view, update, delete, and perform actions on products
