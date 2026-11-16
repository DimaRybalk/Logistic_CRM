import factory
from clients.models import Counterparty
from orders.models import Order,OrderStop
from directory.models import Location,BankingDetail,Contact,Cargo,CargoItem,Vehicle,Trailer
import datetime

class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    company_id = 1
    country = "UA"
    city = factory.Sequence(lambda n: f"city {n}")
    address = factory.Sequence(lambda n: f"address {n}")
    postal_code = "112324"
    region = factory.Sequence(lambda n: f"region {n}")

class BankingDetailFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BankingDetail

    company_id = 1
    legal_form = "TOV"
    title = factory.Sequence(lambda n: f"title {n}")
    tax_number = "2432542312125"
    iban = "DSA124324254"
    is_default = True

class CounterpartyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Counterparty

    company_id = 1
    name = factory.Sequence(lambda n: f"company {n}")
    is_client = True
    is_carrier = False
    location = factory.SubFactory(LocationFactory, company_id = factory.SelfAttribute("..company_id"),)
    payment_details = factory.SubFactory(BankingDetailFactory, company_id = factory.SelfAttribute("..company_id"),)


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    company_id = 1
    is_driver = True
    is_client = False
    is_carrier = False
    is_custom_officer = False
    is_warehouse_worker = False
    first_name = factory.Sequence(lambda n: f"name {n}")
    last_name = factory.Sequence(lambda n: f"last name {n}")
    fathers_name = factory.Sequence(lambda n: f"fathers name {n}")
    counterparty = factory.SubFactory(CounterpartyFactory, company_id = factory.SelfAttribute("..company_id"),)

class CargoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cargo

    company_id = 1
    title = factory.Sequence(lambda n: f"title {n}")
    is_hazardous = False
    requires_temperature_control = False

class CargoItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CargoItem

    name = factory.Sequence(lambda n: f"name {n}")
    packaging_type = "PX"
    quantity = 12
    weight_gross_kg = 2000
    cargo = factory.SubFactory(CargoFactory)


class VehicleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vehicle

    company_id = 1
    carrier = factory.SubFactory(CounterpartyFactory, company_id = factory.SelfAttribute("..company_id"),is_carrier=True,)
    plate_number = "AA2321AA"
    has_adr = False
    is_active = True

class TrailerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trailer

    company_id = 1
    carrier = factory.SubFactory(CounterpartyFactory, company_id = factory.SelfAttribute("..company_id"),is_carrier=True,)
    plate_number = "AA5678XX"
    body_type = "TENT_CURTAIN"
    volume_m3 = 86
    capacity_pallets = 33
    carrying_capacity_kg = 20000
    is_active = True


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    company_id = 1
    responsible_id = 1
    manager_name = "Test"
    client = factory.SubFactory(CounterpartyFactory, company_id = factory.SelfAttribute("..company_id"),)

class OrderStopFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderStop

    company_id = 1
    order = factory.SubFactory(OrderFactory, company_id = factory.SelfAttribute("..company_id"),)
    location = factory.SubFactory(LocationFactory, company_id = factory.SelfAttribute("..company_id"),)
    sequence = factory.Sequence(lambda n: n+1)
    planned_date = datetime.date(2026, 11, 1)
    
