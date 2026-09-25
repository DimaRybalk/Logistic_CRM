from django.db import models

from directory.choices import (
    CurrencyChoices,
    OrderStatusChoices,
    PaymentTermsChoices,
    BorderCrossingChoices,
    StopTypeChoices,
)


class Order(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )

    status = models.CharField(
        max_length=20,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.DRAFT,
        db_index=True,
        verbose_name="Статус заявки"
    )

    # Відповідальний менеджер (дані з JWT токена)
    responsible_id = models.IntegerField(
        db_index=True,
        verbose_name="ID відповідального менеджера"
    )
    manager_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Ім'я відповідального"
    )

    # Сторони договору
    client = models.ForeignKey(
        'clients.Counterparty',
        on_delete=models.SET_NULL,
        related_name="client_orders",
        null=True,
        blank=True,
        limit_choices_to={'is_client': True},
        verbose_name="Клієнт / Замовник"
    )
    carrier = models.ForeignKey(
        'clients.Counterparty',
        on_delete=models.SET_NULL,
        related_name="carrier_orders",
        null=True,
        blank=True,
        limit_choices_to={'is_carrier': True},
        verbose_name="Перевізник"
    )

    # Вантаж
    cargo = models.ForeignKey(
        'directory.Cargo',
        on_delete=models.SET_NULL,
        related_name="orders",
        blank=True,
        null=True,
        verbose_name="Партія вантажу"
    )

    # Транспорт і водій
    vehicle = models.ForeignKey(
        'directory.Vehicle',
        on_delete=models.SET_NULL,
        related_name="orders",
        blank=True,
        null=True,
        verbose_name="Тягач / Авто"
    )
    trailer = models.ForeignKey(
        'directory.Trailer',
        on_delete=models.SET_NULL,
        related_name="orders",
        blank=True,
        null=True,
        verbose_name="Причіп / Напівпричіп"
    )
    driver = models.ForeignKey(
        'directory.Contact',
        on_delete=models.SET_NULL,
        related_name="driver_orders",
        blank=True,
        null=True,
        limit_choices_to={'is_driver': True},
        verbose_name="Водій"
    )

    # Фінанси з клієнтом
    client_currency = models.CharField(
        max_length=5,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.UAH,
        verbose_name="Валюта клієнта"
    )
    client_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Ціна для клієнта"
    )

    # Фінанси з перевізником
    carrier_currency = models.CharField(
        max_length=5,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.UAH,
        verbose_name="Валюта перевізника"
    )
    carrier_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Ставка перевізнику"
    )

    # Умови оплати та логістика
    payments_term = models.CharField(
        max_length=20,
        choices=PaymentTermsChoices.choices,
        default=PaymentTermsChoices.ORIGINALS_7_DAYS,
        blank=True,
        null=True,
        verbose_name="Термін оплати"
    )
    border = models.CharField(
        max_length=20,
        choices=BorderCrossingChoices.choices,
        blank=True,
        null=True,
        verbose_name="Пункт пропуску (NCTS/ЄС)"
    )
    
    notes = models.TextField(blank=True, null=True, verbose_name="Примітки до заявки")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заявка / Замовлення"
        verbose_name_plural = "Заявки / Замовлення"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заявка #{self.id} ({self.client.name if self.client else 'Без клієнта'})"

    # --- Зручні розрахункові поля ---

    @property
    def margin(self):
        """Розрахунок маржі (якщо валюти однакові)"""
        if self.client_price and self.carrier_price and self.client_currency == self.carrier_currency:
            return self.client_price - self.carrier_price
        return None

    @property
    def first_loading(self):
        """Перше місце завантаження (звідки забирати)"""
        stop = self.stops.filter(stop_type=StopTypeChoices.LOADING).order_by("sequence").first()
        return stop.location if stop else None

    @property
    def final_unloading(self):
        """Останнє місце вивантаження (куди доставляти)"""
        stop = self.stops.filter(stop_type=StopTypeChoices.UNLOADING).order_by("sequence").last()
        return stop.location if stop else None

    @property
    def route_title(self):
        """Короткий маршрут для таблиці: 'Київ (UA) -> Варшава (PL)'"""
        load = self.first_loading
        unload = self.final_unloading
        if load and unload:
            return f"{load.city} ({load.country}) ➔ {unload.city} ({unload.country})"
        return "Маршрут не задано"


# ==========================================
# Точки маршруту (зупинки конкретної заявки)
# ==========================================

class OrderStop(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="stops",
        verbose_name="Заявка"
    )
    location = models.ForeignKey(
        'directory.Location',
        on_delete=models.PROTECT,
        related_name="order_stops",
        verbose_name="Адреса / Локація"
    )
    sequence = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Порядок (1, 2, 3...)"
    )
    stop_type = models.CharField(
        max_length=20,
        choices=StopTypeChoices.choices,
        default=StopTypeChoices.LOADING,
        verbose_name="Тип операції"
    )
    planned_date = models.DateField(
        verbose_name="Дата прибуття"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примітки до точки (контакт на складі, рампа)"
    )

    class Meta:
        verbose_name = "Точка маршруту"
        verbose_name_plural = "Точки маршруту"
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "sequence"],
                name="unique_order_stop_sequence"
            )
        ]

    def __str__(self):
        return f"#{self.sequence} {self.get_stop_type_display()}: {self.location.city}"