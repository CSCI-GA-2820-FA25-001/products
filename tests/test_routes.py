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

BASE_URL = "/api/products"

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
    def test_health_check(self):
        """It should return healthy status"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data, {"status": "OK"})

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
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
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
        self.assertTrue(all(Decimal(p["price"]) == test_product.price for p in data))

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

    def test_find_by_price_range_between(self):
        """It should Find Products within a given price range"""
        # Create products with known prices
        p1 = ProductFactory(price=Decimal("5.00"))
        p2 = ProductFactory(price=Decimal("10.00"))
        p3 = ProductFactory(price=Decimal("15.00"))
        p4 = ProductFactory(price=Decimal("25.00"))
        for p in [p1, p2, p3, p4]:
            response = self.client.post(BASE_URL, json=p.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # GET /products?min_price=6&max_price=20
        response = self.client.get(
            BASE_URL, query_string={"min_price": "6", "max_price": "20"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        prices = sorted([Decimal(p["price"]) for p in data])
        self.assertEqual(prices, [Decimal("10.00"), Decimal("15.00")])

    def test_find_by_price_range_min_only(self):
        """It should Find Products with price >= min_price"""
        p1 = ProductFactory(price=Decimal("5.00"))
        p2 = ProductFactory(price=Decimal("10.00"))
        p3 = ProductFactory(price=Decimal("15.00"))
        p4 = ProductFactory(price=Decimal("25.00"))
        for p in [p1, p2, p3, p4]:
            response = self.client.post(BASE_URL, json=p.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # GET /products?min_price=15
        response = self.client.get(BASE_URL, query_string={"min_price": "15"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        prices = sorted([Decimal(p["price"]) for p in data])
        self.assertEqual(prices, [Decimal("15.00"), Decimal("25.00")])

    def test_find_by_price_range_max_only(self):
        """It should Find Products with price <= max_price"""
        p1 = ProductFactory(price=Decimal("5.00"))
        p2 = ProductFactory(price=Decimal("10.00"))
        p3 = ProductFactory(price=Decimal("15.00"))
        p4 = ProductFactory(price=Decimal("25.00"))
        for p in [p1, p2, p3, p4]:
            response = self.client.post(BASE_URL, json=p.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # GET /products?max_price=10
        response = self.client.get(BASE_URL, query_string={"max_price": "10"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        prices = sorted([Decimal(p["price"]) for p in data])
        self.assertEqual(prices, [Decimal("5.00"), Decimal("10.00")])

    def test_find_by_price_range_invalid(self):
        """It should return 400 Bad Request for invalid price range values"""
        response = self.client.get(BASE_URL, query_string={"min_price": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        # error handler may use "message" or "error"
        self.assertTrue("error" in data or "message" in data)

    def test_ui_index(self):
        """It should render the UI page"""
        response = self.client.get("/ui")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Products Admin UI", response.data)

    def test_purchase_product_successful(self):
        """It should successfully Purchase a Product with sufficient inventory"""
        test_product = ProductFactory(available=True, inventory=10)
        response = self.client.post(BASE_URL, json=test_product.serialize())
        product_id = response.get_json()["id"]

        purchase_data = {"quantity": 3}
        response = self.client.post(
            f"{BASE_URL}/{product_id}/purchase",
            json=purchase_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["inventory"], 7)

    def test_purchase_product_unavailable(self):
        """It should reject Purchase when Product is not available"""
        test_product = ProductFactory(available=False, inventory=10)
        response = self.client.post(BASE_URL, json=test_product.serialize())
        product_id = response.get_json()["id"]

        purchase_data = {"quantity": 3}
        response = self.client.post(
            f"{BASE_URL}/{product_id}/purchase",
            json=purchase_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_purchase_product_insufficient_inventory(self):
        """It should reject Purchase when inventory is insufficient"""
        test_product = ProductFactory(available=True, inventory=2)
        response = self.client.post(BASE_URL, json=test_product.serialize())
        product_id = response.get_json()["id"]

        purchase_data = {"quantity": 5}
        response = self.client.post(
            f"{BASE_URL}/{product_id}/purchase",
            json=purchase_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_purchase_product_inventory_unchanged_on_failure(self):
        """It should not change inventory when purchase fails"""
        test_product = ProductFactory(available=False, inventory=10)
        response = self.client.post(BASE_URL, json=test_product.serialize())
        product_id = response.get_json()["id"]

        purchase_data = {"quantity": 3}
        self.client.post(
            f"{BASE_URL}/{product_id}/purchase",
            json=purchase_data,
            content_type="application/json",
        )

        # Check inventory is unchanged
        response = self.client.get(f"{BASE_URL}/{product_id}")
        product = response.get_json()
        self.assertEqual(product["inventory"], 10)

    def test_sort_by_price_ascending(self):
        """It should return 10 products sorted by price ascending"""
        prices = [
            Decimal(x)
            for x in [
                "9.00",
                "1.00",
                "5.00",
                "3.00",
                "7.00",
                "11.00",
                "13.00",
                "19.00",
                "17.00",
                "15.00",
            ]
        ]
        created_ids = []
        for p in prices:
            prod = ProductFactory(price=p)
            resp = self.client.post(BASE_URL, json=prod.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            created_ids.append(resp.get_json()["id"])

        resp = self.client.get(BASE_URL, query_string={"sort": "price", "order": "asc"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 10)

        returned_prices = [Decimal(item["price"]) for item in data]
        self.assertEqual(returned_prices, sorted(prices))

    def test_sort_by_price_descending(self):
        """It should return 10 products sorted by price descending"""
        prices = [
            Decimal(x)
            for x in [
                "2.00",
                "12.00",
                "4.00",
                "8.00",
                "6.00",
                "18.00",
                "10.00",
                "14.00",
                "16.00",
                "20.00",
            ]
        ]
        for p in prices:
            prod = ProductFactory(price=p)
            resp = self.client.post(BASE_URL, json=prod.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(
            BASE_URL, query_string={"sort": "price", "order": "desc"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 10)

        returned_prices = [Decimal(item["price"]) for item in data]
        self.assertEqual(returned_prices, sorted(prices, reverse=True))

    def test_sort_by_price_within_range_ascending(self):
        """It should sort products within a price range ascending"""
        # Create 5 products：5, 10, 15, 20, 25
        for p in [
            Decimal("5.00"),
            Decimal("10.00"),
            Decimal("15.00"),
            Decimal("20.00"),
            Decimal("25.00"),
        ]:
            resp = self.client.post(BASE_URL, json=ProductFactory(price=p).serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(
            BASE_URL,
            query_string={
                "min_price": "10",
                "max_price": "20",
                "sort": "price",
                "order": "asc",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        returned_prices = [Decimal(item["price"]) for item in data]
        self.assertEqual(
            returned_prices, [Decimal("10.00"), Decimal("15.00"), Decimal("20.00")]
        )

    def test_sort_by_price_within_range_descending(self):
        """It should sort products within a price range descending"""
        for p in [
            Decimal("5.00"),
            Decimal("10.00"),
            Decimal("15.00"),
            Decimal("20.00"),
            Decimal("25.00"),
        ]:
            resp = self.client.post(BASE_URL, json=ProductFactory(price=p).serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(
            BASE_URL,
            query_string={
                "min_price": "10",
                "max_price": "20",
                "sort": "price",
                "order": "desc",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        returned_prices = [Decimal(item["price"]) for item in data]
        self.assertEqual(
            returned_prices, [Decimal("20.00"), Decimal("15.00"), Decimal("10.00")]
        )

    def test_sort_by_price_invalid_order_defaults_to_asc(self):
        """It should default to ascending when order is invalid"""
        prices = [Decimal(x) for x in ["9.00", "1.00", "5.00"]]
        for p in prices:
            resp = self.client.post(BASE_URL, json=ProductFactory(price=p).serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(
            BASE_URL, query_string={"sort": "price", "order": "weird"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        returned_prices = [Decimal(item["price"]) for item in data]
        self.assertEqual(returned_prices, sorted(prices))

    def test_sort_query_uses_order_by_clause(self):
        """It should use SQLAlchemy order_by() when result is a BaseQuery"""
        p1 = ProductFactory(name="same", price=Decimal("10.00"))
        p2 = ProductFactory(name="same", price=Decimal("5.00"))
        for p in [p1, p2]:
            resp = self.client.post(BASE_URL, json=p.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(
            BASE_URL, query_string={"name": "same", "sort": "price", "order": "asc"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        prices = [Decimal(item["price"]) for item in data]
        self.assertEqual(prices, [Decimal("5.00"), Decimal("10.00")])

        resp = self.client.get(
            BASE_URL, query_string={"name": "same", "sort": "price", "order": "desc"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        prices = [Decimal(item["price"]) for item in data]
        self.assertEqual(prices, [Decimal("10.00"), Decimal("5.00")])

    def test_bad_request_datavalidationerror(self):
        """It should return 400 via DataValidationError handler"""
        bad_payload = {
            "id": "p-1",
            "name": "Bad",
            "price": "9.99",
            "inventory": 5,
            "available": "yes",
            "description": "x",
            "image_url": "http://x",
        }
        resp = self.client.post("/products", json=bad_payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("Bad Request", data.get("error", ""))
        self.assertIn("Invalid type for boolean", data.get("message", ""))

    def test_method_not_allowed_405(self):
        """It should hit 405 handler for unsupported HTTP method"""
        resp = self.client.patch("/products", json={})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = resp.get_json()
        self.assertEqual(data.get("error"), "Method not Allowed")
        self.assertEqual(data.get("status"), status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_product_not_found(self):
        """It should return 404 when updating a non-existent Product"""
        bogus_id = "does-not-exist"
        payload = ProductFactory(id=bogus_id).serialize()
        resp = self.client.put(f"{BASE_URL}/{bogus_id}", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertTrue("not found" in data.get("message", "").lower())

    def test_purchase_missing_quantity(self):
        """It should return 400 when purchase payload misses quantity"""
        prod = ProductFactory(available=True, inventory=5)
        resp = self.client.post(BASE_URL, json=prod.serialize())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        pid = resp.get_json()["id"]

        resp = self.client.post(
            f"{BASE_URL}/{pid}/purchase", json={}, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("Quantity is required", data.get("message", ""))

    def test_purchase_product_makes_unavailable_when_inventory_zero(self):
        """It should set available to False when inventory reaches zero after purchase"""
        test_product = ProductFactory(available=True, inventory=3)
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product_id = response.get_json()["id"]

        purchase_data = {"quantity": 3}
        response = self.client.post(
            f"{BASE_URL}/{product_id}/purchase",
            json=purchase_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["inventory"], 0)
        self.assertFalse(updated_product["available"])

        response = self.client.get(f"{BASE_URL}/{product_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product = response.get_json()
        self.assertEqual(product["inventory"], 0)
        self.assertFalse(product["available"])
