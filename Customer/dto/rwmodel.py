import datetime

from pydantic import BaseConfig, BaseModel, ConfigDict


def convert_datetime_to_realworld(dt: datetime.datetime) -> str:
    return dt.replace(tzinfo=None).isoformat().replace("+00:00", "Z")


class RWModel(BaseModel):
    """
    A custom Pydantic model base class with the following features:
    - Allows fields to be populated using their alias names (`populate_by_name=True`).
    - Provides a custom JSON encoder for `datetime.datetime` objects, converting them using the `convert_datetime_to_realworld` function.
    - Removes restrictions on protected namespaces by setting `protected_namespaces` to an empty tuple, allowing flexible field naming.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime.datetime: convert_datetime_to_realworld},
        protected_namespaces=(),  # Set protected_namespaces to an empty tuple
    )
