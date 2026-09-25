from django.db import models

from directory.choices import (
    CountryChoices,
    LegalFormChoices,
    ADRClassChoices,
    PackagingTypeChoices,
    BodyTypeChoices,
)


# ==========================================
# Інформація про місцезнаходження
# ==========================================

class Location(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )
    country = models.CharField(
        max_length=5,
        choices=CountryChoices.choices,
        default=CountryChoices.UA,
        db_index=True,
        verbose_name="Країна"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Поштовий індекс"
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Область"
    )
    city = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Місто / Населений пункт"
    )
    address = models.CharField(
        max_length=255,
        verbose_name="Вулиця, номер будинку"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Локація"
        verbose_name_plural = "Локації"
        ordering = ["city", "address"]

    def __str__(self):
        return f"{self.city}, {self.address}"


# ==========================================
# Банківські реквізити
# ==========================================

class BankingDetail(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )
    legal_form = models.CharField(
        max_length=20,
        choices=LegalFormChoices.choices,
        default=LegalFormChoices.TOV,
        verbose_name="Юридична форма власності"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Повна юридична назва компанії"
    )
    tax_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ЄДРПОУ / ІПН / NIP / VAT ID"
    )
    iban = models.CharField(
        max_length=60,
        verbose_name="IBAN / Розрахунковий рахунок"
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Основний рахунок"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примітки"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Банківські реквізити"
        verbose_name_plural = "Банківські реквізити"
        ordering = ["-is_default", "title"]

    def __str__(self):
        return f"{self.title} — {self.iban}"


# ==========================================
# Контактна інформація
# ==========================================

class Contact(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )

    # Ролі контакту
    is_driver = models.BooleanField(default=False, verbose_name="Водій")
    is_client = models.BooleanField(default=False, verbose_name="Клієнт")
    is_carrier = models.BooleanField(default=False, verbose_name="Перевізник")
    is_custom_officer = models.BooleanField(default=False, verbose_name="Митний брокер / Офіцер")
    is_warehouse_worker = models.BooleanField(default=False, verbose_name="Співробітник складу")

    # Загальні персональні дані
    first_name = models.CharField(max_length=100, verbose_name="Ім'я")
    last_name = models.CharField(max_length=100, db_index=True, verbose_name="Прізвище")
    fathers_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="По-батькові")
    phone = models.CharField(max_length=100, blank=True, null=True, verbose_name="Основний номер")
    secondary_phone = models.CharField(max_length=100, blank=True, null=True, verbose_name="Додатковий номер")
    email = models.EmailField(max_length=100, blank=True, null=True, verbose_name="Емейл")

    counterparty = models.ForeignKey(
        'clients.Counterparty',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="contacts",
        verbose_name="Роботодавець / Компанія"
    )

    # Специфічні поля водія
    adr_status = models.CharField(
        max_length=10,
        choices=ADRClassChoices.choices,
        blank=True,
        null=True,
        verbose_name="Клас небезпеки ADR"
    )
    driver_license = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Номер водійського посвідчення"
    )
    passport_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Номер паспорта"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакти"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        full = f"{self.last_name} {self.first_name}"
        if self.fathers_name:
            full += f" {self.fathers_name}"
        return full


# ==========================================
# Вантаж
# ==========================================

class Cargo(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )
    title = models.CharField(
        max_length=255, 
        verbose_name="Загальний опис вантажу"
    )

    # Вимоги до перевезення
    is_hazardous = models.BooleanField(default=False, verbose_name="Небезпечний вантаж (ADR)")
    adr_class = models.CharField(
        max_length=20, 
        choices=ADRClassChoices.choices, 
        blank=True, 
        null=True, 
        verbose_name="Клас ADR"
    )
    requires_temperature_control = models.BooleanField(default=False, verbose_name="Температурний режим")
    temperature_min = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name="Мін. темп. (°C)"
    )
    temperature_max = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name="Макс. темп. (°C)"
    )

    notes = models.TextField(blank=True, null=True, verbose_name="Додаткова інформація")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Партія вантажу"
        verbose_name_plural = "Партії вантажів"

    def __str__(self):
        return self.title


class CargoItem(models.Model):
    cargo = models.ForeignKey(
        'directory.Cargo',
        on_delete=models.CASCADE, 
        related_name="items", 
        verbose_name="Партія вантажу"
    )
    name = models.CharField(max_length=255, verbose_name="Найменування товару")
    packaging_type = models.CharField(
        max_length=5,
        choices=PackagingTypeChoices.choices,
        default=PackagingTypeChoices.EUR_PALLET,
        verbose_name="Основна тара (місце)"
    )
    quantity = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        verbose_name="Кількість основних місць",
        help_text="Кількість палет, бочок тощо. Порожньо, якщо насип."
    )
    weight_gross_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Вага брутто (кг)"
    )
    volume_m3 = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Об'єм (м³)"
    )
    length = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Довжина (см)"
    )
    width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Ширина (см)"
    )
    height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Висота (см)"
    )

    class Meta:
        verbose_name = "Позиція вантажу"
        verbose_name_plural = "Позиції вантажу"

    def __str__(self):
        return f"{self.name} ({self.quantity or 'насип'} шт)"


# ==========================================
# Автомобіль (Тягач)
# ==========================================

class Vehicle(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )
    carrier = models.ForeignKey(
        'clients.Counterparty',
        on_delete=models.CASCADE,
        related_name="vehicles",
        verbose_name="Перевізник / Власник"
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Повна назва ТЗ"
    )
    plate_number = models.CharField(
        max_length=25,
        db_index=True,
        verbose_name="Державний номер авто"
    )
    vin_code = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="VIN-код"
    )
    registration_certificate = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Техпаспорт"
    )
    carrying_capacity_kg = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Вантажопідйомність (кг)"
    )
    has_adr = models.BooleanField(
        default=False,
        verbose_name="Має допуск ADR"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    notes = models.TextField(blank=True, null=True, verbose_name="Примітки")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Транспортний засіб"
        verbose_name_plural = "Транспортні засоби"
        ordering = ["plate_number"]

    def __str__(self):
        return f"{self.name or ''} {self.plate_number}".strip()


# ==========================================
# Напівпричіп
# ==========================================

class Trailer(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )
    carrier = models.ForeignKey(
        'clients.Counterparty',
        on_delete=models.CASCADE,
        related_name="trailers",
        verbose_name="Перевізник / Власник"
    )
    plate_number = models.CharField(
        max_length=25,
        db_index=True,
        verbose_name="Державний номер причепа",
        help_text="Наприклад: AA5678XX"
    )
    body_type = models.CharField(
        max_length=30,
        choices=BodyTypeChoices.choices,
        default=BodyTypeChoices.CURTAINSIDER,
        verbose_name="Тип кузова"
    )
    volume_m3 = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=86.00,
        verbose_name="Об'єм (м³)",
        help_text="Стандарт тент: 86-92 м³, Мега: 100-105 м³"
    )
    capacity_pallets = models.PositiveSmallIntegerField(
        default=33,
        verbose_name="Місткість європалет (шт)",
        help_text="Стандартний напівпричіп вміщує 33 EPAL"
    )
    carrying_capacity_kg = models.PositiveIntegerField(
        default=22000,
        verbose_name="Вантажопідйомність (кг)"
    )
    registration_certificate = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Свідоцтво про реєстрацію причепа"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Причіп / Напівпричіп"
        verbose_name_plural = "Причепи / Напівпричепи"
        ordering = ["plate_number"]

    def __str__(self):
        return f"{self.plate_number} ({self.get_body_type_display()})"