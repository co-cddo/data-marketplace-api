from polyfactory.factories.pydantic_factory import ModelFactory
import model as m
from faker import Faker
import json


class AssetSummaryFactory(ModelFactory[m.BaseAssetSummary]):
    __model__ = m.BaseAssetSummary


class ContactPointFactory(ModelFactory):
    __model__ = m.ContactPoint
    __faker__ = Faker(locale="en_GB")

    @classmethod
    def name(cls) -> str:
        return cls.__faker__.name()

    @classmethod
    def telephone(cls) -> str:
        return cls.__faker__.phone_number()

    @classmethod
    def address(cls) -> str:
        return cls.__faker__.address()

    @classmethod
    def email(cls) -> str:
        return cls.__faker__.company_email()


class DatasetFactory(ModelFactory):
    __model__ = m.Dataset
    __faker__ = Faker()

    @classmethod
    def title(cls) -> str:
        return cls.__faker__.bs()

    @classmethod
    def alternativeTitle(cls) -> str:
        return [cls.__faker__.bs() for i in range(3)]

    @classmethod
    def description(cls) -> str:
        return cls.__faker__.paragraph(nb_sentences=6)

    @classmethod
    def summary(cls) -> str:
        return cls.__faker__.paragraph(nb_sentences=3)

    @classmethod
    def licence(cls) -> str:
        return (
            "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
        )

    @classmethod
    def version(cls) -> str:
        return str(
            cls.__faker__.pydecimal(left_digits=1, right_digits=1, positive=True)
        )

    @classmethod
    def contactPoint(cls) -> m.ContactPoint:
        return ContactPointFactory.build()


asset = DatasetFactory.build()
print(asset.model_dump_json(indent=4))
