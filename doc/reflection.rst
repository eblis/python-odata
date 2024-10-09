.. automodule:: odata.reflector
    :members:
    :exclude-members: MetadataReflector


Reflection
==========
Full example with reflection and enums:

.. code-block:: python
   import logging

   import requests
   import rich

   from odata import ODataService

   requests.packages.urllib3.disable_warnings()


   def test_trippin(console):
       proxy = {'http': '', 'https': ''}

       session = requests.Session()

       session.trust_env = False
       session.verify = False
       session.proxies.update(proxy)

       service = ODataService(
           url="https://services.odata.org/v4/TripPinServiceRW",
           console=console,
           session=session,
           reflect_output_package="generated.trippin")

       # although the import will work if placed here, you will still have a weird error about a null URL on the first run
       # that it because the base is not correctly configured on first run, you need to run the code a second time
       import generated.trippin
       People = generated.trippin.People

       q = service.query(People)

       values = q.all()
       for value in values:
           console.rule(f"People {value.FirstName} {value.LastName}")
           service.values(value)


   if __name__ == "__main__":
       logging.basicConfig(level="DEBUG")
       console = rich.console.Console()
       test_trippin(console)



