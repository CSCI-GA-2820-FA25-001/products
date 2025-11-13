Feature: Manage Products via the Admin UI
  As an eCommerce manager
  I want to manage products through the web interface
  So that I can create, view, update, delete, and perform actions on products

Background:
    Given the application is started

Scenario: The application is running
    When I visit the "Home Page"
    Then I should see "Product REST API Service" in the title
    And I should not see "404 Not Found"