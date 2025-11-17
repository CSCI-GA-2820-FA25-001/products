Feature: Manage Products via the Admin UI
  As an eCommerce manager
  I want to manage products through the web interface
  So that I can create, view, update, delete, and perform actions on products

Background:
    Given the following products
        | id         | name     | price     | description | image_url   | available | inventory |
        | 00001      | candy    | 4.2       | tasty       |             | False     | 0         |
        | 00002      | car      | 5.5       | good        |             | True      | 5         |
        | 00003      | wood     | 6.0       |             |             | True      | 3         |
        | 00004      | bike     | 9.9       |             |             | True      | 3         |

Scenario: The application is running
    When I visit the "Home Page"
    Then I should see "Product REST API Service" in the title
    And I should not see "404 Not Found"

Scenario: Delete a Product by ID
    When I visit the "Home Page"
    And I set the "Product ID" to "00002"
    And I press the "Delete Product" button
    Then I should see the message "Product 00002 deleted successfully!"
    When I press the "List All Products" button
    Then I should see the message "Loaded 3 product(s)"
    And I should see "candy" in the results
    And I should see "wood" in the results
    And I should see "bike" in the results
    And I should not see "car" in the results