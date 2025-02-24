
from dataclasses import dataclass

@dataclass
class ODataServerFlags:
  skip_null_properties: bool = False
  provide_odata_type_annotation: bool = True
  odata_bind_requires_slash: bool = False
