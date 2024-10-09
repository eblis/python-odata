.. automodule:: odata.service
    :members:
    :exclude-members: ODataError

Service
==========

reflect_entites
---------------
If set to `True` then the service will call $metadata endpoint and collect all classes, entities, enums from it.
If set to `False` then the service will not reflect the entities.

If set to the default value `None` then the service will reflect the entities if the package pointing to `reflect_output_package` is not available, but if it's available it will not reflect the entities again.
Basically it will check if reflection has been already done and not do it again. **It will not check if anything has changed on server**, so if you know the entities have changed on the server you need to delete the package file so it can be re-generated.


reflect_output_package
----------------------
If configured to a package name (e.g. `"generated.northwind"`) will emit a python file with that name will all the reflected entities which can then be reused.
