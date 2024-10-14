<%page args="entity, property, values"/>\
<%
    property_name = values['name'].replace("@", "_").replace("-", "_")
    property_type = type(property)
    simple_type = property_type.__name__.split(".")[-1]
    if simple_type not in type_translations:
        print(property, property_type, values)
        property.primary_key = False
        full_type = values['type'].split(".")[-1]
    else:
        full_type = type_translations[simple_type]
    if property.is_collection:
        full_type = "list[" + simple_type + "]"
    if property.is_nullable:
        full_type = "Optional[" + full_type + "]"
%>\
    ${property_name}: ${full_type} = ${simple_type}("${values['name']}"\
  % if property.primary_key:
, primary_key=True\
  % endif
  % if property.is_collection:
, is_collection=True\
  % endif
, is_nullable=${property.is_nullable}\
  % if property.is_computed_value:
, is_computed_value=True\
  % endif
  % if hasattr(property, "type_class"):
, type_class=${property.type_class.__name__}\
  % endif
  % if hasattr(property, 'enum_class'):
, enum_class=${property.enum_class.__name__}\
  % endif
)