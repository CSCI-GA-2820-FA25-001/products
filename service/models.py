"""
Models for Product

All of the models are stored in this module
"""

# from decimal import Decimal, ROUND_HALF_UP
import logging
from flask_sqlalchemy import SQLAlchemy


logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


# def _round_to_cents(value):
#     """Return Decimal rounded to 0.01 using HALF_UP; allow int/str/float/Decimal."""
#     if value is None:
#         return None
#     try:
#         d = Decimal(str(value))
#     except Exception as e:
#         raise DataValidationError(f"Invalid price: {value}") from e
#     return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Product(db.Model):
    id = db.Column(db.String(63), primary_key=True, nullable=False)
    name = db.Column(db.String(127), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    available = db.Column(db.Boolean, nullable=False, default=True)

    """
    Class that represents a Product
    """

    ##################################################
    # Table Schema
    ##################################################

    # Todo: Place the rest of your schema here...

    def __repr__(self):
        return f"<Product {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Product to the database
        """
        logger.info("Creating %s", self.name)
        if not self.id:
            raise DataValidationError(
                "Product id must be provided when not autogenerating."
            )
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        """
        Updates a Product to the database
        """
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
        """Removes a Product from the data store"""
        logger.info("Deleting %s", self.name)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Product into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price if self.price is not None else None,
            "image_url": self.image_url,
            "available": self.available,
        }

    def deserialize(self, data):
        """
        Deserializes a Product from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.id = data["id"]
            self.name = data["name"]
            self.price = data["price"]
            self.description = data.get("description")
            self.image_url = data.get("image_url")
            if isinstance(data["available"], bool):
                self.available = data["available"]
            else:
                raise DataValidationError(
                    "Invalid type for boolean [available]: "
                    + str(type(data["available"]))
                )
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Product: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Product: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the Products in the database"""
        logger.info("Processing all Products")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a Product by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_id(cls, id):
        """Returns the Product with the given ID

        Args:
            id (int): the ID of the Product you want to match
        """
        logger.info("Processing ID query for %s ...", id)
        return cls.query.filter(cls.id == id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all Products with the given name

        Args:
            name (string): the name of the Products you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_description(cls, description: str) -> list:
        """Returns all Products matching a given description

        :param description: the description of the Products you want to match
        :type description: str

        :return: a collection of Products with that description
        :rtype: list
        """
        logger.info("Processing description query for %s ...", description)
        return cls.query.filter(cls.description == description)

    @classmethod
    def find_by_price(cls, price: float) -> list:
        """Returns all Products with the given price

        :param price: the price of the Products you want to match
        :type price: float

        :return: a collection of Products with that price
        :rtype: list
        """
        logger.info("Processing price query for %s ...", price)
        return cls.query.filter(cls.price == price)

    @classmethod
    def find_by_availability(cls, available: bool = True) -> list:
        """Returns all Products by their availability

        :param available: True for products that are available
        :type available: bool

        :return: a collection of Products that are available
        :rtype: list
        """
        if not isinstance(available, bool):
            raise TypeError("Invalid availability, must be of type boolean")
        logger.info("Processing available query for %s ...", available)
        return cls.query.filter(cls.available == available)

    @classmethod
    def find_by_image_url(cls, image_url: str) -> list:
        """Returns all Products with the given image URL

        :param image_url: the image URL of the Products you want to match
        :type image_url: str

        :return: a collection of Products with that image URL
        :rtype: list
        """
        logger.info("Processing image URL query for %s ...", image_url)
        return cls.query.filter(cls.image_url == image_url)
