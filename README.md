# python-odata

A simple library for read/write access to OData services.

- Supports OData version 4.0
- Requires JSON format support from the service
- Should work on both Python 2.x and 3.x

## Documentation

Available on [readthedocs.org](https://python-odata.readthedocs.io/en/latest/index.html)

## Dependencies

- requests >= 2.0
- python-dateutil
- rich >= 13.3.1

## Demo

Reading data from the Northwind service.

```python
import requests
from datetime import datetime

# you can only import this on the second run, the first run will create the package
# import generated 
from odata import ODataService
session = requests.Session()

url = 'http://services.odata.org/V4/Northwind/Northwind.svc/'
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
values = query.all()
values = query \
    .filter((OrderDetails.Order.Employee.HomePhone.contains("555")) | (OrderDetails.Order.Employee.City == "London")) \
    .filter(OrderDetails.Order.Employee.FirstName.lacks("Steven")) \
    .filter(OrderDetails.Order.OrderDate >= datetime(year=1990, month=5, day=1, hour=10, minute=10, second=59, tzinfo=pytz.UTC))\
    .expand(OrderDetails.Order, OrderDetails.Order.Employee) \
    .order_by(OrderDetails.Order.ShipCountry.asc()) \
    .limit(10) \
    .all()
for order_details in values:
    print(f"Order {order_details.OrderID}")
    service.values(order_details)
    service.values(order_details.Order)
    service.values(order_details.Order.Employee)
```

Writing changes. Note that the real Northwind service is _read-only_
and the data modifications do not work against it.

```python
import datetime

Order = Service.entities['Order']
Employee = Service.entities['Employee']

empl = Service.query(Employee).first()

query = Service.query(Order)
query = query.filter(Order.ShipCity == 'Berlin')

for order in query:
    order.ShippedDate = datetime.datetime.utcnow() 
    order.Employee = empl
    Service.save(order)
```
