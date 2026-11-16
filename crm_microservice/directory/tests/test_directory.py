from decimal import Decimal

import pytest
from django.urls import reverse
from core.factories import CounterpartyFactory, LocationFactory,BankingDetailFactory,ContactFactory,CargoFactory,CargoItemFactory,VehicleFactory,TrailerFactory
from rest_framework.test import APIClient

from directory.models import Contact, Location, Cargo, CargoItem, Vehicle
from .helpers import create_token

# Location

@pytest.mark.django_db
def test_show_others_locations():
    location_other = LocationFactory(company_id = 2)
    location1 = LocationFactory()
    token = create_token(1, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("location-list")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    ids = [item["id"] for item in data]
    assert location1.id in ids
    assert location_other.id not in ids

@pytest.mark.django_db
def test_show_others_location_by_id():
    location_other = LocationFactory(company_id = 2)
    location1 = LocationFactory()
    token = create_token(1, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("location-detail", kwargs={"pk": location_other.id})
    response = api_client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_patch_others_location():
    token = create_token(1, "OWNER")
    location_other = LocationFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_data = {
        "postal_code" : "new",
    }
    url = reverse("location-detail", kwargs={"pk": location_other.id})
    response = api_client.patch(url, new_data, format="json")
    assert response.status_code == 404
    location_other.refresh_from_db()
    assert location_other.postal_code != "new"

@pytest.mark.django_db
def test_delete_others_location():
    token = create_token(1, "OWNER")
    location_other = LocationFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    url = reverse("location-detail", kwargs={"pk": location_other.id})
    response = api_client.delete(url)
    assert response.status_code == 404
    location_other.refresh_from_db()
    assert location_other.company_id == 2


@pytest.mark.django_db
def test_create_location():
    expected_company_id = 1
    token = create_token(expected_company_id, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    data = {
        "city": "dsfdv",
        "address": "fdwfgwegew",
    }
    url = reverse("location-list")
    response = api_client.post(url, data)
    assert response.status_code == 201
    data = response.json()
    assert data["company_id"] == expected_company_id

@pytest.mark.django_db
def test_show_anonymous():
    url = reverse("location-list")
    api_client = APIClient()
    response = api_client.get(url)
    assert response.status_code == 401

@pytest.mark.django_db
def test_permissions_rights():
    location = LocationFactory(company_id = 1)
    token = create_token(1, "VIEWER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("location-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 1
    data = {
            "city": "dsfdv",
            "address": "fdwfgwegew",
        }
    url = reverse("location-list")
    response = api_client.post(url, data)
    assert response.status_code == 403
    assert not Location.objects.filter(city="dsfdv").exists()

@pytest.mark.django_db
def test_driver_permissions():
    location = LocationFactory(company_id = 1)
    token = create_token(1, "DRIVER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("location-list")
    response = api_client.get(url)
    assert response.status_code == 403
    

# BankingDetail

@pytest.mark.django_db
def test_others_details():
    token = create_token(company_id=1,role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    detail1 = BankingDetailFactory(company_id=1)
    detail2 = BankingDetailFactory(company_id=2)
    url = reverse("banking-detail-list")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    ids = [item["id"] for item in data]
    assert detail1.id in ids
    assert detail2.id not in ids


@pytest.mark.django_db
def test_show_other_detail_by_id():
    token = create_token(company_id=1, role= "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    detail1 = BankingDetailFactory(company_id=1)
    detail2 = BankingDetailFactory(company_id=2)
    url = reverse("banking-detail-detail", kwargs={"pk": detail2.id})
    response = api_client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_patch_other():
    token = create_token(1, "OWNER")
    banking2 = BankingDetailFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_data = {
        "title": "Hacked title"
    }
    url = reverse("banking-detail-detail", kwargs={"pk": banking2.id})
    response = api_client.patch(url, new_data, format="json")
    assert response.status_code == 404
    banking2.refresh_from_db()
    assert banking2.title != "Hacked title"

@pytest.mark.django_db
def test_delete_others_details():
    token = create_token(1, "OWNER")
    banking2 = BankingDetailFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    url = reverse("banking-detail-detail", kwargs={"pk": banking2.id})
    response = api_client.delete(url)
    assert response.status_code == 404
    banking2.refresh_from_db()
    assert banking2.company_id == 2

@pytest.mark.django_db
def test_request_banking_without_token():
    api_client = APIClient()
    banking = BankingDetailFactory(company_id = 1)
    url = reverse("banking-detail-list")
    response = api_client.get(url)
    assert response.status_code == 401

@pytest.mark.django_db
def test_viewer_rights_details():
    token = create_token(company_id=1, role="VIEWER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    banking = BankingDetailFactory()
    url = reverse("banking-detail-list")
    response = api_client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_driver_rights_details():
    token = create_token(company_id=1, role="DRIVER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    banking = BankingDetailFactory()
    url = reverse("banking-detail-list")
    response = api_client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_iban_corect():
    token = create_token(company_id=1, role="OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    detail = BankingDetailFactory(company_id = 1)
    new_data = {
        "iban" : "ua12 4343 3255 1232 1234"
    }
    url = reverse("banking-detail-detail", kwargs={"pk": detail.id})
    response = api_client.patch(url, new_data)
    assert response.status_code == 200
    data = response.json()
    detail.refresh_from_db()
    assert data["iban"] == "UA124343325512321234"

@pytest.mark.django_db
def test_iban_length():
    token = create_token(company_id=1, role="OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    detail = BankingDetailFactory(company_id = 1)
    new_data = {
        "iban" : "ua12"
    }
    url = reverse("banking-detail-detail", kwargs={"pk": detail.id})
    response = api_client.patch(url, new_data)
    assert response.status_code == 400
      

@pytest.mark.django_db
def test_default_banking_changes():
    token = create_token(company_id=1, role="OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    detail = BankingDetailFactory(company_id = 1, is_default = True)
    detail2 = BankingDetailFactory(company_id = 1, is_default = False)
    new_data = {
        "is_default" : True
    }
    url = reverse("banking-detail-detail", kwargs={"pk": detail2.id})
    response = api_client.patch(url, new_data)
    assert response.status_code == 200
    detail.refresh_from_db()
    detail2.refresh_from_db()
    assert detail.is_default == False

# Contact

@pytest.mark.django_db
def test_show_others_contacts():
    token = create_token(company_id=1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    contact1 = ContactFactory(company_id = 1)
    contact2 = ContactFactory(company_id = 2)
    url = reverse("contact-list")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    ids = [item["id"] for item in data]
    assert contact1.id in ids
    assert contact2.id not in ids

@pytest.mark.django_db
def test_show_others_contact_by_id():
    contact_other = ContactFactory(company_id = 2)
    contact1 = ContactFactory()
    token = create_token(1, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("contact-detail", kwargs={"pk": contact_other.id})
    response = api_client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_patch_others_contact():
    token = create_token(1, "OWNER")
    contact_other = ContactFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_data = {
        "first_name" : "new",
    }
    url = reverse("contact-detail", kwargs={"pk": contact_other.id})
    response = api_client.patch(url, new_data, format="json")
    assert response.status_code == 404
    contact_other.refresh_from_db()
    assert contact_other.first_name != "new"

@pytest.mark.django_db
def test_delete_others_contact():
    token = create_token(1, "OWNER")
    contact_other = ContactFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    url = reverse("contact-detail", kwargs={"pk": contact_other.id})
    response = api_client.delete(url)
    assert response.status_code == 404
    contact_other.refresh_from_db()
    assert contact_other.company_id == 2

@pytest.mark.django_db
def test_create_contacts():
    expected_company_id = 1
    token = create_token(expected_company_id, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    data = {
    "first_name": "Ivan",
    "last_name": "Petrenko",
}
    url = reverse("contact-list")
    response = api_client.post(url, data)
    assert response.status_code == 201
    data = response.json()
    assert data["company_id"] == expected_company_id

@pytest.mark.django_db
def test_request_contact_without_token():
    api_client = APIClient()
    contact = ContactFactory(company_id = 1)
    url = reverse("contact-list")
    response = api_client.get(url)
    assert response.status_code == 401

@pytest.mark.django_db
def test_viewer_rights_contacts():
    token = create_token(company_id=1, role="VIEWER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    contact = ContactFactory()
    url = reverse("contact-list")
    response = api_client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_driver_rights_contacts():
    token = create_token(company_id=1, role="DRIVER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    contact = ContactFactory()
    url = reverse("contact-list")
    response = api_client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_creation_with_other_counterparty():
    token = create_token(company_id=1, role="OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    other_cp = CounterpartyFactory(company_id=2)
    data = {
        "first_name": "Ivan",
        "last_name": "Petrenko",
        "counterparty_id": other_cp.id,
    }
    url = reverse("contact-list")
    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    assert not Contact.objects.filter(last_name = "Petrenko").exists()

@pytest.mark.django_db
def test_creation_with_yours_counterparty():
    token = create_token(company_id=1, role="OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    cp = CounterpartyFactory(company_id=1)
    data = {
        "first_name": "Ivan",
        "last_name": "Petrenko",
        "counterparty_id": cp.id,
    }
    url = reverse("contact-list")
    response = api_client.post(url, data, format="json")
    assert response.status_code == 201
    assert Contact.objects.filter(last_name = "Petrenko").exists()

@pytest.mark.django_db
def test_contacts_filter():
    token = create_token(company_id = 1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    contact = ContactFactory(company_id = 1, is_driver = True)
    contact2 = ContactFactory(company_id = 1, is_driver = False)
    q_params = "?is_driver=true"
    url = reverse("contact-list")
    response = api_client.get(url + q_params)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    ids = [item["id"] for item in data]
    assert contact.id in ids
    assert contact2.id not in ids

# Cargo

@pytest.mark.django_db
def test_show_others_cargo():
    cargo_other = CargoFactory(company_id = 2)
    cargo1 = CargoFactory()
    token = create_token(1, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("cargo-list")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    ids = [item["id"] for item in data]
    assert cargo1.id in ids
    assert cargo_other.id not in ids

@pytest.mark.django_db
def test_show_others_cargo_by_id():
    cargo_other = CargoFactory(company_id = 2)
    cargo1 = CargoFactory()
    token = create_token(1, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("cargo-detail", kwargs={"pk": cargo_other.id})
    response = api_client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_patch_others_cargo():
    token = create_token(1, "OWNER")
    cargo_other = CargoFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_data = {
        "title" : "new",
    }
    url = reverse("cargo-detail", kwargs={"pk": cargo_other.id})
    response = api_client.patch(url, new_data, format="json")
    assert response.status_code == 404
    cargo_other.refresh_from_db()
    assert cargo_other.title != "new"

@pytest.mark.django_db
def test_delete_others_cargo():
    token = create_token(1, "OWNER")
    cargo_other = CargoFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    url = reverse("cargo-detail", kwargs={"pk": cargo_other.id})
    response = api_client.delete(url)
    assert response.status_code == 404
    cargo_other.refresh_from_db()
    assert cargo_other.company_id == 2

@pytest.mark.django_db
def test_create_cargo():
    expected_company_id = 1
    token = create_token(expected_company_id, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    data = {
        "title": "dsfdv",
    }
    url = reverse("cargo-list")
    response = api_client.post(url, data)
    assert response.status_code == 201
    data = response.json()
    assert data["company_id"] == expected_company_id

@pytest.mark.django_db
def test_show_cargo_anonymous():
    url = reverse("cargo-list")
    api_client = APIClient()
    response = api_client.get(url)
    assert response.status_code == 401

@pytest.mark.django_db
def test_cargo_viewer_rights():
    token = create_token(company_id=1, role = "VIEWER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    cargo = CargoFactory(company_id = 1)
    new_data = {
            "title": "dsfdv",
        }
    url = reverse("cargo-list")
    response_get = api_client.get(url)
    assert response_get.status_code == 200
    response_post = api_client.post(url, new_data, format="json")
    assert response_post.status_code == 403


@pytest.mark.django_db
def test_cargo_driver_rights():
    token = create_token(company_id=1, role = "DRIVER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    cargo = CargoFactory(company_id = 1)
    url = reverse("cargo-list")
    response_get = api_client.get(url)
    assert response_get.status_code == 403

@pytest.mark.django_db
def test_create_cargo_with_items():
    token = create_token(company_id=1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_data = {
        "title" : "dsadd",
        "cargo_items" : [{"name" : "dsds", "weight_gross_kg" : 2000},]
    }
    url = reverse("cargo-list")
    response = api_client.post(url, new_data, format = "json")
    assert response.status_code == 201
    data = response.json()
    cargo = Cargo.objects.get(id=data["id"])
    assert cargo.items.count() == 1
    assert cargo.items.first().name == "dsds"

@pytest.mark.django_db
def test_patch_cargo_with_items():
    token = create_token(company_id=1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_cargo = CargoFactory(company_id = 1)
    cargo_item = CargoItemFactory(cargo=new_cargo, name = "old")
    new_data = {
        "cargo_items" : [{"name" : "new", "weight_gross_kg" : 2000},]
    }
    url = reverse("cargo-detail", kwargs={"pk": new_cargo.id})
    response = api_client.patch(url, new_data, format = "json")
    assert response.status_code == 200
    new_cargo.refresh_from_db()
    data = response.json()
    cargo = Cargo.objects.get(id = data["id"])
    assert cargo.items.count() == 1
    assert cargo.items.first().name == "new"
    assert not CargoItem.objects.filter(id = cargo_item.id).exists()

@pytest.mark.django_db
def test_check_cargo_temperature():
    token = create_token(company_id = 1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_data = {
        "title" : "title",
        "requires_temperature_control" : True
    }
    url = reverse("cargo-list")
    response = api_client.post(url, new_data, format="json")
    assert response.status_code == 400
    assert not Cargo.objects.filter(title="title").exists()


@pytest.mark.django_db
def test_check_cargo_temperature_validation():
    token = create_token(company_id = 1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_data = {
        "title" : "title",
        "requires_temperature_control" : True,
        "temperature_min": 25,
        "temperature_max": 20,
    }
    url = reverse("cargo-list")
    response = api_client.post(url, new_data, format="json")
    assert response.status_code == 400
    assert not Cargo.objects.filter(title="title").exists()
    
@pytest.mark.django_db
def test_check_cargoitem_volume_calculation():
    token = create_token(company_id = 1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_data = {
            "title" : "title",
            "cargo_items" : [{"name" : "new", "weight_gross_kg" : 2000, "length": 200, "width" : 200, "height": 200},]
        }
    url = reverse("cargo-list")
    response = api_client.post(url, new_data, format="json")
    assert response.status_code == 201
    data = response.json()
    cargo = Cargo.objects.get(id = data["id"])
    assert cargo.items.first().volume_m3 == Decimal("8.00")

# Vehicle

@pytest.mark.django_db
def test_show_others_vehicle():
    vehicle_other = VehicleFactory(company_id = 2)
    vehicle1 = VehicleFactory()
    token = create_token(1, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("vehicle-list")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    ids = [item["id"] for item in data]
    assert vehicle1.id in ids
    assert vehicle_other.id not in ids

@pytest.mark.django_db
def test_show_others_vehicle_by_id():
    vehicle_other = VehicleFactory(company_id = 2)
    vehicle1 = VehicleFactory()
    token = create_token(1, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse("vehicle-detail", kwargs={"pk": vehicle_other.id})
    response = api_client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_patch_others_vehicle():
    token = create_token(1, "OWNER")
    vehicle_other = VehicleFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    carrier = CounterpartyFactory(company_id = 1, is_carrier = True)
    new_data = {
        "carrier_id" : carrier.id,
    }
    url = reverse("vehicle-detail", kwargs={"pk": vehicle_other.id})
    response = api_client.patch(url, new_data, format="json")
    assert response.status_code == 404
    vehicle_other.refresh_from_db()
    assert vehicle_other.carrier_id != 1

@pytest.mark.django_db
def test_delete_others_vehicle():
    token = create_token(1, "OWNER")
    vehicle_other = VehicleFactory(company_id = 2)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    url = reverse("vehicle-detail", kwargs={"pk": vehicle_other.id})
    response = api_client.delete(url)
    assert response.status_code == 404
    vehicle_other.refresh_from_db()
    assert vehicle_other.company_id == 2

@pytest.mark.django_db
def test_create_vehicle():
    expected_company_id = 1
    token = create_token(expected_company_id, "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    carrier = CounterpartyFactory(company_id = 1, is_carrier = True)
    data = {
        "carrier_id": carrier.id,
        "name": "MAN TGX",
        "plate_number": "AA1234BB",
        "vin_code": "WMA06XZZ6TW123456",
        "registration_certificate": "ABC123456",
        "carrying_capacity_kg": 20000,
        "has_adr": True,
        "is_active": True,
        "notes": "Test vehicle",
    }
    url = reverse("vehicle-list")
    response = api_client.post(url, data)
    assert response.status_code == 201
    data = response.json()
    assert data["company_id"] == expected_company_id

@pytest.mark.django_db
def test_show_vehicle_anonymous():
    url = reverse("vehicle-list")
    api_client = APIClient()
    response = api_client.get(url)
    assert response.status_code == 401

@pytest.mark.django_db
def test_vehicle_viewer_rights():
    token = create_token(company_id=1, role = "VIEWER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    vehicle = VehicleFactory(company_id = 1)
    carrier = CounterpartyFactory(company_id = 1, is_carrier = True)
    new_data = {
        "carrier_id": carrier.id,
        "name" : "dfdsf"
        }
    url = reverse("vehicle-list")
    response_get = api_client.get(url)
    assert response_get.status_code == 200
    response_post = api_client.post(url, new_data, format="json")
    assert response_post.status_code == 403


@pytest.mark.django_db
def test_vehicle_driver_rights():
    token = create_token(company_id=1, role = "DRIVER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    vehicle = VehicleFactory(company_id = 1)
    url = reverse("vehicle-list")
    response_get = api_client.get(url)
    assert response_get.status_code == 403

@pytest.mark.django_db
def test_vehicle_plate_validation():
    token = create_token(company_id=1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_vehicle = VehicleFactory(company_id = 1)
    carrier = CounterpartyFactory(company_id = 1, is_carrier = True)
    data = {
        "carrier_id": carrier.id,
        "name": "MAN TGX",
        "plate_number": "aa 1234 bb",
        }
    url = reverse("vehicle-detail", kwargs={"pk": new_vehicle.id})
    response = api_client.patch(url, data, format="json")
    assert response.status_code == 200
    vehicle = Vehicle.objects.get(id = new_vehicle.id)
    assert vehicle.plate_number == "AA1234BB"

@pytest.mark.django_db
def test_vehicle_plate_validation_length():
    token = create_token(company_id=1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_vehicle = VehicleFactory(company_id = 1, plate_number = "AA1234BB")
    carrier = CounterpartyFactory(company_id = 1, is_carrier = True )
    data = {
        "carrier_id": carrier.id,
        "name": "MAN TGX",
        "plate_number": "aa2",
        }
    url = reverse("vehicle-detail", kwargs={"pk": new_vehicle.id})
    response = api_client.patch(url, data, format="json")
    assert response.status_code == 400
    new_vehicle.refresh_from_db()
    assert new_vehicle.plate_number == "AA1234BB"

@pytest.mark.django_db
def test_vehicle_plate_validation_vin():
    token = create_token(company_id=1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    new_vehicle = VehicleFactory(company_id = 1, vin_code = "WMA06XZZ6TW123456")
    carrier = CounterpartyFactory(company_id = 1, is_carrier = True )
    data = {
        "carrier_id": carrier.id,
        "name": "MAN TGX",
        "vin_code": "aa2",
        }
    url = reverse("vehicle-detail", kwargs={"pk": new_vehicle.id})
    response = api_client.patch(url, data, format="json")
    assert response.status_code == 400
    new_vehicle.refresh_from_db()
    assert new_vehicle.vin_code == "WMA06XZZ6TW123456"    

@pytest.mark.django_db
def test_vehicle_creation_with_client_id():
    token = create_token(company_id=1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    carrier = CounterpartyFactory(company_id = 1, is_carrier = False )
    data = {
        "carrier_id": carrier.id,
        "name": "MAN TGX",
        "vin_code": "WMA06XZZ6TW123456",
        "plate_number": "AA1234BB"
        }
    url = reverse("vehicle-list")
    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    

@pytest.mark.django_db
def test_vehicle_creation_with_others_carrier():
    token = create_token(company_id=1, role = "OWNER")
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION = f"Bearer {token}")
    carrier = CounterpartyFactory(company_id = 2, is_carrier = True )
    data = {
        "company_id": 1,
        "carrier_id": carrier.id,
        "name": "MAN TGX",
        "vin_code": "WMA06XZZ6TW123456",
        "plate_number": "AA1234BB"
        }
    url = reverse("vehicle-list")
    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    assert "carrier_id" in response.json()