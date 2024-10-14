# -*- coding: utf-8 -*-
import dataclasses
import numbers
from dataclasses import dataclass

from odata.property import QueryBase, StringProperty, IntegerProperty, FloatProperty, CollectionQueryBase


@dataclass
class ComplexType:
    pass


class ComplexTypeProperty(QueryBase, CollectionQueryBase):
    """
    A property that contains a ComplexType object

    :param name: Name of the property in the endpoint
    :param type_class: A subclass of ComplexType
    """

    def __init__(self, name, type_class=ComplexType, is_collection: bool = False, is_nullable: bool = True):
        """
        :type name: str
        """
        super(ComplexTypeProperty, self).__init__(name)
        self.name = name
        self.is_collection = is_collection
        self.is_nullable = is_nullable
        self.type_class = type_class

    def __getattr__(self, item):
        fields = dataclasses.fields(self.type_class)
        for field in fields:
            if field.name == item:
                return ComplexTypeProperty(f"{self.name}/{field.name}", field.type, is_nullable=False)
        raise AttributeError(f"{item} does not exist in {self.name}")

    def __set__(self, instance, value):
        instance.__odata_complex_type__ = value

    def serialize(self, value):
        if isinstance(value, list):
            data = []
            for i in value:
                data.append(self._serialize(i))
            return data
        else:
            return self._serialize(value)

    def _serialize(self, value):
        data = dict()
        for candidate in dir(self):
            member = getattr(self, candidate)
            if issubclass(member, ComplexType):
                value = member.serialize()
            else:
                value = member
            data[candidate] = value
        return data

    def deserialize(self, value):
        if isinstance(value, list):
            self.is_collection = True
            data = []
            for i in value:
                data.append(self._deserialize(i))
            return data
        else:
            return self._deserialize(value)

    def _deserialize(self, value):
        data = self.type_class

        for member in dataclasses.fields(self.type_class):
            value[member.name] = self._build_recursive(member, value)

        return data(**value)

    def _build_recursive(self, member, value):
        if dataclasses.is_dataclass(member.type):
            for child in dataclasses.fields(member.type):
                value[member.name][child.name] = self._build_recursive(child, value[member.name])
            return member.type(**value[member.name])
        return value[member.name]

    def escape_value(self, value):
        if isinstance(value, str):
            return StringProperty.escape_value(self, value)
        if isinstance(value, int):
            return IntegerProperty.escape_value(self, value)
        if isinstance(value, float):
            return FloatProperty.escape_value(self, value)

        raise NotImplementedError()