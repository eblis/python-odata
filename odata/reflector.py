# -*- coding: utf-8 -*-

"""
Entity reflection
=================

Entities parsed from metadata endpoint can be written (emitted) to a local file.
This file can then be used without having to re-parse the metadata file every time the service starts.
This is especially useful if parsing the metadata endpoint takes a long time.

In order to perform the reflection you have to specify the package name where the classes will be written and
also to set the flag for reflection.

.. code-block:: python

    service = ODataService(
        url="http://services.odata.org/V4/Northwind/Northwind.svc/",
        session=session,
        reflect_entities=True,
        reflect_output_package="generated.northwind")

This will generate all the classes in `generated` folder, `northwind.py` file, and can be referenced by `generated.northwind.<Entity>`.
The first classes will be the types defined in $metadata enpoint and the queryable entities will follow after.


Using reflected types
---------------------
After the file has been generated you do not need to keep generating it over and over,
although it might help if any changes are done to the service.
However, any changes done to the service will be detected only on the second run,
as the classes are already imported when the file is re-written - if you're using the generated classes that is.

.. code-block:: python

    service = ODataService(
        url="http://services.odata.org/V4/Northwind/Northwind.svc/",
        session=session,
        base=generated.northwind.ReflectionBase,
        reflect_entities=False)

So in order to use the generated files you have to run the code twice, first time to generate the data files, then later to use them.

When using the generated files you **have to specify the base class** as `ReflectionBase` defined in your generated file.

This is necessary because of some internal stuff that the original library did and I haven't been bothered enough by this to try and change it.

Type hints
----------

One nice advantage of using the generated classes is that you can have typing hints and your IDE can help you see the members each class has,
making calls and queries a lot easier to implement.

.. code-block:: python

    service = ODataService(
        url="http://services.odata.org/V4/Northwind/Northwind.svc/",
        session=session,
        base=generated.northwind.ReflectionBase,
        reflect_entities=True,
        reflect_output_package="generated.northwind")
    OrderDetails = generated.northwind.Order_Details

    q = service.query(generated.northwind.Customers)
    q = q.filter(generated.northwind.Customers.ContactTitle.startswith('Sales'))
    q = q.filter(generated.northwind.Customers.PostalCode == '68306')
    data = q.first()

    query = service.query(OrderDetails)
    values = query \\
        .filter((OrderDetails.Order.Employee.HomePhone.contains("555")) | (OrderDetails.Order.Employee.City == "London")) \\
        .filter(OrderDetails.Order.Employee.FirstName.lacks("Steven")) \\
        .expand(OrderDetails.Order) \\
        .order_by(OrderDetails.Order.ShipCountry.asc()) \\
        .limit(10) \\
        .all()

"""

import rich
from io import StringIO
from pathlib import Path
from enum import EnumMeta

from mako import exceptions
from mako.lookup import TemplateLookup
from mako.runtime import Context

from odata.complextype import ComplexType

type_translations = {
    "StringProperty": "str",
    "IntegerProperty": "int",
    "NavigationProperty": "caca",  # fixme: is this used ?
    "DatetimeProperty": "datetime.datetime",
    "DecimalProperty": "decimal.Decimal",
    "FloatProperty": "float",
    "BooleanProperty": "bool",
    "UUIDProperty": "uuid.UUID",
    "EnumTypeProperty": "str",
    "LocationProperty": "str",
}


class MetadataReflector:
    def __init__(self,
                 metadata_url: str,
                 entities: dict[str, "EntitySetCategories"],
                 types: dict[str, "EntityBase"],
                 package: str,
                 console: rich.console.Console,
                 quiet: bool = False):
        self.package = package
        self.metadata_url = metadata_url
        self.entities = entities
        self.types = types
        self.console = console
        self.quiet = quiet

    def write_reflected_types(self):
        template_folder = Path(__file__).parent / "reflect-templates"
        lookup = TemplateLookup(directories=[str(template_folder)], output_encoding="utf-8", preprocessor=[lambda x: x.replace("\r\n", "\n")])
        template = lookup.get_template("main.mako")

        types = {k: v for k, v in self.types.items() if not isinstance(v, EnumMeta)}
        enum_types = {k: v for k, v in self.types.items() if isinstance(v, EnumMeta)}

        simple_types = {k: v for k, v in self.types.items() if issubclass(v, ComplexType)}
        types = {k: v for k, v in types.items() if k not in simple_types}

        buffer = StringIO()
        context = Context(buffer,
                          entities=self.entities,
                          types=types,
                          enum_types=enum_types,
                          simple_types=simple_types,
                          all_types=self.types,
                          type_translations=type_translations,
                          package=self.package,
                          metadata_url=self.metadata_url)
        with self.console.status("Loading metadata"):
            try:
                template.render_context(context)
            except Exception as ex:
                self.console.print(exceptions.text_error_template(lookup).render())
                raise ex

        output_path = Path(self.package.replace(".", "/")).with_suffix(".py")
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True)

        value = buffer.getvalue()
        with output_path.open("wt") as fout:
            fout.write(value)
        # exit(2)
