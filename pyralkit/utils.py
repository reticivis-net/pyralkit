import json

import dacite
from dateutil.parser import isoparse

from .models import *

T = typing.TypeVar("T")


def parse_dict_to_obj(data: dict, objtype: typing.Type[T]) -> T:
    return dacite.from_dict(
        data_class=objtype,
        data=data,
        config=dacite.Config(
            type_hooks={datetime.datetime: isoparse, datetime.date: isoparse},
            cast=[int, PKPrivacy],
        ),
    )


def parse_bytes_to_obj(data: bytes, objtype: typing.Type[T]) -> T:
    return parse_dict_to_obj(json.loads(data), objtype)


def custom_asdict_factory(data):
    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj

    return dict((k, convert_value(v)) for k, v in data)
