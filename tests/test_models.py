######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Test cases for Product Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from decimal import Decimal
from wsgi import app
from service.models import Product, DataValidationError, db
from .factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


#  B A S E   T E S T   C A S E S
######################################################################
class TestCaseBase(TestCase):
    """Base Test Case for common setup"""

    # pylint: disable=duplicate-code
    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()


######################################################################
#   P R O D U C T  M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(TestCaseBase):
    """Test Cases for Product Model"""

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should create a Product"""

        product = ProductFactory()
        product.create()
        self.assertIsNotNone(product.id)
        self.assertIsNotNone(product.name)
        self.assertIsNotNone(product.price)
        self.assertIsNotNone(product.available)
        self.assertIsNotNone(product.inventory)

        found = Product.all()
        self.assertEqual(len(found), 1)

        data = Product.find(product.id)
        self.assertEqual(data.name, product.name)
        self.assertEqual(data.price, product.price)
        self.assertEqual(data.available, product.available)
        self.assertEqual(data.inventory, product.inventory)

    def test_create_no_id(self):
        """It should not Create a Product with no id"""
        product = ProductFactory()
        logging.debug(product)
        product.id = None
        self.assertRaises(DataValidationError, product.create)

    def test_create_a_bad_product(self):
        """It should create a bad Product"""
        product = ProductFactory()
        product.name = None
        self.assertRaises(DataValidationError, product.create)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        logging.debug(product)

        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
        self.assertEqual(found_product.image_url, product.image_url)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.inventory, product.inventory)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        logging.debug(product)
        product.create()
        logging.debug(product)
        self.assertIsNotNone(product.id)
        # Change it and save it
        product.description = "new description"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "new description")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "new description")

    def test_update_no_id(self):
        """It should not Update a Product with no id"""
        product = ProductFactory()
        logging.debug(product)
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_delete_no_id(self):
        """It should not Delete a Product with no id"""
        product = ProductFactory()
        logging.debug(product)
        product.id = None
        self.assertRaises(DataValidationError, product.delete)

    def test_serialize_a_product(self):
        """It should serialize a Product"""
        product = ProductFactory()
        data = product.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], product.id)
        self.assertIn("name", data)
        self.assertEqual(data["name"], product.name)
        self.assertIn("price", data)
        self.assertEqual(data["price"], product.price)
        self.assertIn("description", data)
        self.assertEqual(data["description"], product.description)
        self.assertIn("image_url", data)
        self.assertEqual(data["image_url"], product.image_url)
        self.assertIn("available", data)
        self.assertEqual(data["available"], product.available)
        self.assertIn("inventory", data)
        self.assertEqual(data["inventory"], product.inventory)

    def test_deserialize_a_product(self):
        """It should de-serialize a Product"""
        data = ProductFactory().serialize()
        product = Product()
        product.deserialize(data)
        self.assertNotEqual(product, None)
        self.assertEqual(product.id, data["id"])
        self.assertEqual(product.name, data["name"])
        self.assertEqual(product.price, data["price"])
        self.assertEqual(product.description, data["description"])
        self.assertEqual(product.image_url, data["image_url"])
        self.assertEqual(product.available, data["available"])
        self.assertEqual(product.inventory, data["inventory"])

    def test_deserialize_missing_data(self):
        """It should not deserialize a Product with missing data"""
        data = {"id": 1, "name": "Kitty"}
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)

    def test_deserialize_attribute_error(self):
        """It should raise DataValidationError when an AttributeError occurs"""

        class BrokenData:
            """A dummy data class used in tests to simulate AttributeError when accessing keys."""

            def __getitem__(self, key):
                """Always raise AttributeError to simulate broken data access."""
                raise AttributeError("boom")  # Simulate AttributeError

            def keys(self):
                """meaningless method just to silence lint."""
                return []

        bad_data = BrokenData()
        product = Product()

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(bad_data)

        self.assertIn("Invalid attribute", str(context.exception))

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)

    def test_deserialize_bad_available(self):
        """It should not deserialize a bad available attribute"""
        test_product = ProductFactory()
        data = test_product.serialize()
        data["available"] = "true"
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)


######################################################################
#  T E S T   E X C E P T I O N   H A N D L E R S
######################################################################
class TestExceptionHandlers(TestCaseBase):
    """Product Model Exception Handlers"""

    @patch("service.models.db.session.commit")
    def test_create_exception(self, exception_mock):
        """It should catch a create exception"""
        exception_mock.side_effect = Exception()
        product = ProductFactory()
        self.assertRaises(DataValidationError, product.create)

    @patch("service.models.db.session.commit")
    def test_update_exception(self, exception_mock):
        """It should catch a update exception"""
        exception_mock.side_effect = Exception()
        product = ProductFactory()
        self.assertRaises(DataValidationError, product.update)

    @patch("service.models.db.session.commit")
    def test_delete_exception(self, exception_mock):
        """It should catch a delete exception"""
        exception_mock.side_effect = Exception()
        product = ProductFactory()
        self.assertRaises(DataValidationError, product.delete)


######################################################################
#  Q U E R Y   T E S T   C A S E S
######################################################################
class TestModelQueries(TestCaseBase):
    """Product Model Query Tests"""

    def test_find_product(self):
        """It should Find a Product by ID"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        logging.debug(products)
        # make sure they got saved
        self.assertEqual(len(Product.all()), 5)
        # find the 2nd product in the list
        product = Product.find(products[1].id)
        self.assertEqual(product.id, product.id)
        self.assertEqual(product.name, product.name)
        self.assertEqual(product.description, product.description)
        self.assertEqual(product.price, product.price)
        self.assertEqual(product.image_url, product.image_url)
        self.assertEqual(product.available, product.available)
        self.assertEqual(product.inventory, product.inventory)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_price_range_between(self):
        """It should Find Products within a price range (min & max inclusive)"""
        p1 = ProductFactory(price=Decimal("5.00"))
        p1.create()
        p2 = ProductFactory(price=Decimal("10.00"))
        p2.create()
        p3 = ProductFactory(price=Decimal("15.00"))
        p3.create()
        p4 = ProductFactory(price=Decimal("25.00"))
        p4.create()

        found = Product.find_by_price_range(Decimal("6.00"), Decimal("20.00"))
        prices = sorted([p.price for p in found])
        self.assertEqual(prices, [Decimal("10.00"), Decimal("15.00")])

    def test_find_by_price_range_min_only(self):
        """It should Find Products with price >= min_price"""
        p1 = ProductFactory(price=Decimal("5.00"))
        p1.create()
        p2 = ProductFactory(price=Decimal("10.00"))
        p2.create()
        p3 = ProductFactory(price=Decimal("15.00"))
        p3.create()
        p4 = ProductFactory(price=Decimal("25.00"))
        p4.create()

        found = Product.find_by_price_range(min_price=Decimal("15.00"))
        prices = sorted([p.price for p in found])
        self.assertEqual(prices, [Decimal("15.00"), Decimal("25.00")])

    def test_find_by_price_range_max_only(self):
        """It should Find Products with price <= max_price"""
        p1 = ProductFactory(price=Decimal("5.00"))
        p1.create()
        p2 = ProductFactory(price=Decimal("10.00"))
        p2.create()
        p3 = ProductFactory(price=Decimal("15.00"))
        p3.create()
        p4 = ProductFactory(price=Decimal("25.00"))
        p4.create()

        found = Product.find_by_price_range(max_price=Decimal("10.00"))
        prices = sorted([p.price for p in found])
        self.assertEqual(prices, [Decimal("5.00"), Decimal("10.00")])
