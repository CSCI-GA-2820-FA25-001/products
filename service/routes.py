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

# spell: ignore Rofrano jsonify restx dbname
"""
Product Service with Swagger

Paths:
------
GET / - Displays service info
GET /api/ui - Displays Admin UI
GET /api/health - Health check endpoint
GET /api/products - Returns a list of all Products
GET /api/products/{id} - Returns the Product with a given id
POST /api/products - Creates a new Product record in the database
PUT /api/products/{id} - Updates a Product record in the database
DELETE /api/products/{id} - Deletes a Product record in the database
POST /api/products/{id}/purchase - Purchases a Product (reduces inventory)
"""

from decimal import Decimal, InvalidOperation
from flask import request, render_template, jsonify
from flask import current_app as app  # Import Flask application
from flask_restx import Api, Resource, fields, reqparse, inputs
from werkzeug.exceptions import MethodNotAllowed, HTTPException
from service.models import Product, DataValidationError
from service.common import status  # HTTP Status Codes


######################################################################
# Configure the Root route before OpenAPI
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    return (
        jsonify(
            service="Product REST API Service",
            version="1.0",
            description="This service manages products for an eCommerce platform.",
            list_url=request.host_url.rstrip("/") + "/api/products",
        ),
        status.HTTP_200_OK,
    )


######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Product REST API Service",
    description="This service manages products for an eCommerce platform.",
    default="products",
    default_label="Product operations",
    doc="/apidocs",
    prefix="/api",
)


######################################################################
# Custom error handler for 405 Method Not Allowed
######################################################################
@api.errorhandler(MethodNotAllowed)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors"""
    return {"error": "Method not Allowed", "status": 405, "message": str(error)}, 405


######################################################################
# Generic JSON error handlers for the API
######################################################################
@api.errorhandler(DataValidationError)
def handle_data_validation(error):
    """Return JSON for DataValidationError as HTTP 400"""
    app.logger.error("Data validation error: %s", error)
    return {
        "status": status.HTTP_400_BAD_REQUEST,
        "error": "Bad Request",
        "message": str(error),
    }, status.HTTP_400_BAD_REQUEST


@api.errorhandler(HTTPException)
def handle_http_exception(error):
    """
    Ensure all HTTPException (404, 415, etc.) return JSON instead of the default HTML error pages.
    """
    app.logger.error("HTTPException: %s", error)
    return {
        "status": error.code,
        "error": error.name,
        "message": error.description,
    }, error.code


######################################################################
# Define the models for Swagger documentation
######################################################################
create_model = api.model(
    "Product",
    {
        "name": fields.String(required=True, description="The name of the Product"),
        "description": fields.String(
            required=False, description="The description of the Product"
        ),
        "price": fields.Fixed(
            decimals=2, required=True, description="The price of the Product"
        ),
        "available": fields.Boolean(
            required=True, description="Is the Product available for purchase?"
        ),
        "image_url": fields.String(
            required=False, description="The image URL of the Product"
        ),
        "inventory": fields.Integer(
            required=False, description="The inventory count of the Product", default=0
        ),
    },
)

product_model = api.inherit(
    "ProductModel",
    create_model,
    {
        "id": fields.String(
            readOnly=True, description="The unique id assigned internally by service"
        ),
    },
)

purchase_model = api.model(
    "Purchase",
    {
        "quantity": fields.Integer(
            required=True, description="The quantity to purchase", min=1
        ),
    },
)


######################################################################
# Query string arguments for listing products
######################################################################
product_args = reqparse.RequestParser()
product_args.add_argument(
    "id", type=str, location="args", required=False, help="Filter by Product ID"
)
product_args.add_argument(
    "name", type=str, location="args", required=False, help="Filter by Product name"
)
product_args.add_argument(
    "description",
    type=str,
    location="args",
    required=False,
    help="Filter by Product description",
)
product_args.add_argument(
    "price", type=str, location="args", required=False, help="Filter by exact price"
)
product_args.add_argument(
    "min_price",
    type=str,
    location="args",
    required=False,
    help="Filter by minimum price",
)
product_args.add_argument(
    "max_price",
    type=str,
    location="args",
    required=False,
    help="Filter by maximum price",
)
product_args.add_argument(
    "available",
    type=inputs.boolean,
    location="args",
    required=False,
    help="Filter by availability",
)
product_args.add_argument(
    "image_url",
    type=str,
    location="args",
    required=False,
    help="Filter by image URL",
)
product_args.add_argument(
    "sort",
    type=str,
    location="args",
    required=False,
    choices=["price"],
    help="Sort by field (currently only 'price' supported)",
)
product_args.add_argument(
    "order",
    type=str,
    location="args",
    required=False,
    default="asc",
    help="Sort order: 'asc' or 'desc'",
)


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def abort(error_code: int, message: str):
    """Logs errors before aborting"""
    app.logger.error(message)
    api.abort(error_code, message)


def check_content_type(content_type: str) -> None:
    """Ensure that the request has the given Content-Type."""
    ct = request.headers.get("Content-Type", None)
    if not ct:
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )
    if ct != content_type:
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )


def _handle_price_filter(price):
    """Handle price equality filtering"""
    try:
        price_value = Decimal(price)
    except (InvalidOperation, TypeError):
        abort(status.HTTP_400_BAD_REQUEST, f"Invalid price value: {price}")
    return Product.find_by_price(price_value)


def _handle_price_range_filter(min_price, max_price):
    """Handle price range filtering"""
    try:
        min_val = Decimal(min_price) if min_price else None
        max_val = Decimal(max_price) if max_price else None
    except (InvalidOperation, TypeError):
        abort(status.HTTP_400_BAD_REQUEST, "Invalid price range values")
    return Product.find_by_price_range(min_val, max_val)


def _get_filtered_products(args):
    """Return filtered Products based on query params in priority order."""
    products = []

    product_id = args.get("id")
    name = args.get("name")
    description = args.get("description")
    price = args.get("price")
    min_price = args.get("min_price")
    max_price = args.get("max_price")
    available = args.get("available")
    image_url = args.get("image_url")

    if product_id:
        app.logger.info("Find by id: %s", product_id)
        products = Product.find_by_id(product_id)
    elif name:
        app.logger.info("Find by name: %s", name)
        products = Product.find_by_name(name)
    elif description:
        app.logger.info("Find by description: %s", description)
        products = Product.find_by_description(description)
    elif price:
        products = _handle_price_filter(price)
    elif min_price or max_price:
        products = _handle_price_range_filter(min_price, max_price)
    elif available is not None:
        app.logger.info("Find by availability: %s", available)
        products = Product.find_by_availability(available)
    elif image_url:
        app.logger.info("Find by image_url: %s", image_url)
        products = Product.find_by_image_url(image_url)
    else:
        app.logger.info("Find all")
        products = Product.all()

    return products


def _apply_sort(products, sort, order):
    """Apply sorting if requested; handle BaseQuery and list consistently. Return a list."""
    if sort == "price":
        if hasattr(products, "order_by"):  # SQL side
            col = Product.price
            return products.order_by(col.asc() if order == "asc" else col.desc()).all()
        reverse = order == "desc"
        return sorted(products, key=lambda p: p.price, reverse=reverse)

    if hasattr(products, "all"):
        return products.all()
    return list(products) if not isinstance(products, list) else products


######################################################################
#  PATH: /products/{id}
######################################################################
@api.route("/products/<product_id>")
@api.param("product_id", "The Product identifier")
class ProductResource(Resource):
    """
    ProductResource class

    Allows the manipulation of a single Product
    GET /products/{id} - Returns a Product with the id
    PUT /products/{id} - Update a Product with the id
    DELETE /products/{id} - Deletes a Product with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE A PRODUCT
    # ------------------------------------------------------------------
    @api.doc("get_product")
    @api.response(404, "Product not found")
    @api.marshal_with(product_model)
    def get(self, product_id):
        """
        Retrieve a single Product

        This endpoint will return a Product based on its id
        """
        app.logger.info("Request to Retrieve a product with id [%s]", product_id)
        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Product with id '{product_id}' was not found.",
            )
        app.logger.info("Returning product: %s", product.name)
        return product.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING PRODUCT
    # ------------------------------------------------------------------
    @api.doc("update_product")
    @api.response(404, "Product not found")
    @api.response(400, "The posted Product data was not valid")
    @api.response(415, "Invalid Content-Type")
    @api.expect(product_model)
    @api.marshal_with(product_model)
    def put(self, product_id):
        """
        Update a Product

        This endpoint will update a Product based on the body that is posted
        """
        app.logger.info("Request to Update a product with id [%s]", product_id)
        check_content_type("application/json")
        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Product with id '{product_id}' was not found.",
            )
        app.logger.debug("Payload = %s", api.payload)
        data = api.payload
        product.deserialize(data)
        product.update()
        app.logger.info("Product with ID: %s updated.", product.id)
        return product.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A PRODUCT
    # ------------------------------------------------------------------
    @api.doc("delete_product")
    @api.response(204, "Product deleted")
    def delete(self, product_id):
        """
        Delete a Product

        This endpoint will delete a Product based on the id specified in the path
        """
        app.logger.info("Request to Delete a product with id [%s]", product_id)
        product = Product.find(product_id)
        if product:
            app.logger.info("Product with ID: %s found.", product.id)
            product.delete()
            app.logger.info("Product with ID: %s delete complete.", product_id)

        return "", status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /products
######################################################################
@api.route("/products", strict_slashes=False)
class ProductCollection(Resource):
    """Handles all interactions with collections of Products"""

    # ------------------------------------------------------------------
    # LIST ALL PRODUCTS
    # ------------------------------------------------------------------
    @api.doc("list_products")
    @api.expect(product_args, validate=True)
    @api.marshal_list_with(product_model)
    def get(self):
        """Returns all of the Products"""
        app.logger.info("Request for product list")

        args = product_args.parse_args()
        sort = args.get("sort")
        order = (args.get("order") or "asc").lower()
        if order not in ("asc", "desc"):
            order = "asc"

        products = _get_filtered_products(args)
        products = _apply_sort(products, sort, order)

        results = [product.serialize() for product in products]
        app.logger.info("Returning %d products", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD A NEW PRODUCT
    # ------------------------------------------------------------------
    @api.doc("create_product")
    @api.response(400, "The posted data was not valid")
    @api.response(415, "Invalid Content-Type")
    @api.expect(create_model)
    @api.marshal_with(product_model, code=201)
    def post(self):
        """
        Create a Product

        This endpoint will create a Product based on the data in the body that is posted
        """
        app.logger.info("Request to Create a Product...")
        check_content_type("application/json")
        product = Product()
        app.logger.debug("Payload = %s", api.payload)
        product.deserialize(api.payload)
        product.create()
        app.logger.info("Product with new id [%s] saved!", product.id)
        location_url = api.url_for(
            ProductResource, product_id=product.id, _external=True
        )
        return (
            product.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
#  PATH: /products/{id}/purchase
######################################################################
@api.route("/products/<product_id>/purchase")
@api.param("product_id", "The Product identifier")
class PurchaseResource(Resource):
    """Purchase actions on a Product"""

    @api.doc("purchase_product")
    @api.response(404, "Product not found")
    @api.response(400, "Invalid purchase request")
    @api.response(409, "Product not available or insufficient inventory")
    @api.expect(purchase_model)
    @api.marshal_with(product_model)
    def post(self, product_id):
        """
        Purchase a Product

        This endpoint will reduce the inventory of a product based on the quantity purchased
        """
        app.logger.info("Request to Purchase product with id [%s]", product_id)
        check_content_type("application/json")

        # Find the product
        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Product with id '{product_id}' was not found.",
            )

        # Get the purchase quantity from request
        data = api.payload
        quantity = data.get("quantity") if data else None

        # Validate quantity
        if quantity is None:
            abort(status.HTTP_400_BAD_REQUEST, "Quantity is required for purchase")

        if not isinstance(quantity, int) or quantity <= 0:
            abort(status.HTTP_400_BAD_REQUEST, "Quantity must be a positive integer")

        # Check if product is available
        if not product.available:
            abort(
                status.HTTP_409_CONFLICT,
                f"Product '{product.name}' is not available for purchase",
            )

        # Check if sufficient inventory exists
        if product.inventory < quantity:
            abort(
                status.HTTP_409_CONFLICT,
                f"Insufficient inventory. Requested: {quantity}, Available: {product.inventory}",
            )

        # Update inventory
        product.inventory -= quantity
        if product.inventory == 0:
            product.available = False
        product.update()

        app.logger.info(
            "Product with ID: %s purchased. Quantity: %d, Remaining inventory: %d",
            product_id,
            quantity,
            product.inventory,
        )

        return product.serialize(), status.HTTP_200_OK


######################################################################
# Regular Flask routes - defined AFTER Flask-RESTX resources
######################################################################
@app.route("/ui")
def ui_index():
    """Render the Admin UI page"""
    return render_template("index.html", base_url="")


@app.route("/health")
def health_check():
    """Let them know our heart is still beating"""
    app.logger.info("Request for health check")
    return jsonify(status="OK"), status.HTTP_200_OK
