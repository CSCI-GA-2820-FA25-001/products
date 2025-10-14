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
TestProduct API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from decimal import Decimal
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Product
from .factories import ProductFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)

BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    def _create_products(self, count: int = 1) -> list:
        """Factory method to create product in bulk"""
        product = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test product",
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            product.append(test_product)
        return product

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    ############################################################
    # Utility function to bulk create product
    ############################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["service"], "Product REST API Service")

    def test_delete_product(self):
        """It should Delete a Product"""
        test_product = self._create_products(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_product(self):
        """It should Delete a Product even if it doesn't exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_a_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["id"], test_product.id)
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["image_url"], test_product.image_url)
        self.assertEqual(new_product["available"], test_product.available)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["id"], test_product.id)
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        # self.assertEqual(new_product["price"], test_product.price)
        self.assertEqual(Decimal(str(new_product["price"])), test_product.price)
        self.assertEqual(new_product["image_url"], test_product.image_url)
        self.assertEqual(new_product["available"], test_product.available)

    def test_create_product_missing_content_type(self):
        """It should fail when Content-Type header is missing"""
        response = self.client.post(f"{BASE_URL}", data="{}")  # No Content-Type header
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_invalid_content_type(self):
        """It should fail when Content-Type is incorrect"""
        response = self.client.post(
            f"{BASE_URL}",
            json={"name": "Bad Product"},
            headers={"Content-Type": "text/plain"},  # Wrong content type
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------
    def test_get_product(self):
        """It should Get a single Product"""
        # get the id of a product
        test_product = self._create_products(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_product.name)

    def test_get_product_not_found(self):
        """It should not Get a Product thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_product(self):
        """It should Update an existing Product"""
        # create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the product
        new_product = response.get_json()
        logging.debug(new_product)
        new_product["name"] = "new name"
        new_product["description"] = "new description"
        new_product["price"] = Decimal("12.5")
        new_product["image_url"] = "unknown"
        new_product["available"] = True
        response = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["name"], "new name")
        self.assertEqual(updated_product["description"], "new description")
        self.assertEqual(Decimal(updated_product["price"]), Decimal("12.5"))
        self.assertEqual(updated_product["image_url"], "unknown")
        self.assertEqual(updated_product["available"], True)

    # ----------------------------------------------------------
    # TEST LIST
    # ----------------------------------------------------------
    def test_get_product_list(self):
        """It should Get a list of Products"""
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_find_by_id(self):
        """It should Find Products by ID"""
        test_product = self._create_products(1)[0]
        response = self.client.get(BASE_URL, query_string={"id": test_product.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # You can assert at least that the returned list includes the correct ID
        self.assertTrue(any(p["id"] == test_product.id for p in data))

    def test_find_by_name(self):
        """It should Find Products by name"""
        test_product = self._create_products(1)[0]
        response = self.client.get(BASE_URL, query_string={"name": test_product.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertTrue(all(p["name"] == test_product.name for p in data))

    def test_find_by_description(self):
        """It should Find Products by description"""
        test_product = self._create_products(1)[0]
        response = self.client.get(
            BASE_URL, query_string={"description": test_product.description}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertTrue(all(p["description"] == test_product.description for p in data))

    def test_find_by_price_valid(self):
        """It should Find Products by valid price"""
        test_product = self._create_products(1)[0]
        response = self.client.get(
            BASE_URL, query_string={"price": str(test_product.price)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertTrue(all(str(p["price"]) == str(test_product.price) for p in data))

    def test_find_by_price_invalid(self):
        """It should return 400 for invalid price"""
        response = self.client.get(BASE_URL, query_string={"price": "not-a-number"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_find_by_availability_true(self):
        """It should Find Products that are available"""
        self._create_products(3)
        response = self.client.get(BASE_URL, query_string={"available": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_find_by_availability_false(self):
        """It should Find Products that are unavailable"""
        self._create_products(3)
        response = self.client.get(BASE_URL, query_string={"available": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_find_by_image_url(self):
        """It should Find Products by image_url"""
        test_product = self._create_products(1)[0]
        response = self.client.get(
            BASE_URL, query_string={"image_url": test_product.image_url}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertTrue(all(p["image_url"] == test_product.image_url for p in data))

    def test_find_all_products(self):
        """It should Find all Products when no query params given"""
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)
