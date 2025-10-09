"""
Test Factory to make fake objects for testing
"""
import random
import factory
from service.models import Product


class ProductFactory(factory.Factory):
    """Creates fake products that you don't have to feed"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Product
    id = factory.Sequence(lambda n: f"SKU-{n:06d}") 
    # Required fields
    name = factory.Faker("word")
    # 2-decimal price; your model rounds anyway, but we’ll format correctly
    price = factory.LazyFunction(lambda: round(random.uniform(1, 999), 2))

    # Optional fields
    description = factory.Faker("sentence", nb_words=8)
    image_url = factory.Faker("image_url")
    available = True

    # Todo: Add your other attributes here...
