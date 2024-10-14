<%page args="entity, property, values"/>\
<%
    property_name = values['name'].replace("@", "_").replace("-", "_")
    property_type = type(property)
    simple_type = property_type.__name__.split(".")[-1]
    static_type = False
    if simple_type not in type_translations:
        static_type = True
        print(property, property_type, values)
        full_type = values['type'].split(".")[-1]
    else:
        full_type = type_translations[simple_type]
    if property.is_collection:
        full_type = "list[" + simple_type + "]"
    if property.is_nullable:
        full_type = "Optional[" + full_type + "]"
%>\
    ${property_name}: ${full_type}