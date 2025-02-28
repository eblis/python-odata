from dataclasses import dataclass


@dataclass
class ODataServerFlags:
    """
    Server specific flags for an OData server.
    """

    """
    If null/none/empty properties should be skipped/not sent to the server.
    """
    skip_null_properties: bool = False

    """
    If we should specify @odata.type property when updating entities.
    """
    provide_odata_type_annotation: bool = True

    """
    If we should add a slash before the @odata.bind annotation.
    """
    odata_bind_requires_slash: bool = False
