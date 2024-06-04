<%page args="name, entity"/>\
<% short_name = name.split(".")[-1] %>\
${short_name} = Enum("${short_name}", {\
%for prop in entity:
"${prop.name}" : "${prop.value}",\
%endfor
})