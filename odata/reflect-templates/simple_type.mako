
<%page args="name, entity"/>\
<% short_name = name.split(".")[-1] %>\
<% base_type = "(" + entity.__bases__[0].__name__ + ")" if len(entity.__bases__) > 0 else '' %>\
@dataclass
class ${short_name}${base_type}:
  <%
    schema = entity.__odata_schema__
  %>\
  # Simple properties
  %for prop in schema['properties']:
<% attr = getattr(entity, prop['name']) %>\
<%include file="simple_property.mako" args="entity=entity, property=attr, values=prop"/>
  %endfor
