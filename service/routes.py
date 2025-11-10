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
Product Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Product
"""

from decimal import Decimal, InvalidOperation
from flask import jsonify, request, url_for, abort, render_template
from flask import current_app as app  # Import Flask application
from service.models import Product
from service.common import status  # HTTP Status Codes


@app.route("/ui")
def ui_index():
    """Render the Admin UI page"""
    return render_template("index.html", base_url="")


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    response = {
        "service": "Product REST API Service",
        "version": "1.0",
        "description": "This service manages products for an eCommerce platform.",
        "list_url": request.host_url.rstrip("/") + url_for("list_products"),
    }
    return jsonify(response), status.HTTP_200_OK


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# READ A PRODUCT
######################################################################
@app.route("/products/<string:product_id>", methods=["GET"])
def get_product(product_id):
    """
    Retrieve a single Product

    This endpoint will return a Product based on it's id
    """
    app.logger.info("Request to Retrieve a product with id [%s]", product_id)

    # Attempt to find the Product and abort if not found
    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found."
        )

    app.logger.info("Returning product: %s", product.name)
    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# CREATE A NEW PET
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Create a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    product = Product()
    # Get the data from the request and deserialize it
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product.deserialize(data)

    # Save the new Product to the database
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    # Return the location of the new Product
    location_url = url_for("get_product", product_id=product.id, _external=True)

    return (
        jsonify(product.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# UPDATE AN EXISTING PET
######################################################################
@app.route("/products/<string:product_id>", methods=["PUT"])
def update_products(product_id):
    """
    Update a Product

    This endpoint will update a Product based the body that is posted
    """
    app.logger.info("Request to Update a product with id [%s]", product_id)
    check_content_type("application/json")

    # Attempt to find the Product and abort if not found
    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found."
        )

    # Update the Product with the new data
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product.deserialize(data)

    # Save the updates to the database
    product.update()

    app.logger.info("Product with ID: %s updated.", product.id)
    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


######################################################################
# Checks the ContentType of a request
######################################################################
def check_content_type(content_type) -> None:
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# LIST ALL PETS
######################################################################
def _handle_price_filter(price):
    """Handle price equality filtering"""
    try:
        price_value = Decimal(price)
    except (InvalidOperation, TypeError):
        abort(400, f"Invalid price value: {price}")
    return Product.find_by_price(price_value)


def _handle_price_range_filter(min_price, max_price):
    """Handle price range filtering"""
    try:
        min_val = Decimal(min_price) if min_price else None
        max_val = Decimal(max_price) if max_price else None
    except (InvalidOperation, TypeError):
        abort(400, "Invalid price range values")
    return Product.find_by_price_range(min_val, max_val)


@app.route("/products", methods=["GET"])
def list_products():
    """Returns all of the Products"""
    app.logger.info("Request for product list")

    products = []

    # Parse any arguments from the query string
    product_id = request.args.get("id")
    name = request.args.get("name")
    description = request.args.get("description")
    price = request.args.get("price")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    available = request.args.get("available")
    image_url = request.args.get("image_url")

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
    elif available:
        app.logger.info("Find by availability: %s", available)
        available_value = available.lower() in ["true", "yes", "1"]
        products = Product.find_by_availability(available_value)
    elif image_url:
        app.logger.info("Find by image_url: %s", image_url)
        products = Product.find_by_image_url(image_url)
    else:
        app.logger.info("Find all")
        products = Product.all()

    results = [product.serialize() for product in products]
    app.logger.info("Returning %d products", len(results))
    return jsonify(results), status.HTTP_200_OK


######################################################################
# DELETE A PRODUCT
######################################################################
@app.route("/products/<string:product_id>", methods=["DELETE"])
def delete_products(product_id):
    """
    Delete a Product

    This endpoint will delete a Product based the id specified in the path
    """
    app.logger.info("Request to Delete a product with id [%s]", product_id)

    # Delete the Product if it exists
    product = Product.find(product_id)
    if product:
        app.logger.info("Product with ID: %d found.", product.id)
        product.delete()

    app.logger.info("Product with ID: %d delete complete.", product_id)
    return {}, status.HTTP_204_NO_CONTENT
