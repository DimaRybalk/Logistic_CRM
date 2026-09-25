from django.db import models


class Counterparty(models.Model):
    company_id = models.IntegerField(
        db_index=True,
        verbose_name="ID компанії-експедитора"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Назва компанії"
    )
    is_client = models.BooleanField(
        default=False,
        verbose_name="Клієнт"
    )
    is_carrier = models.BooleanField(
        default=False,
        verbose_name="Перевізник"
    )

    # Юридична / фактична адреса компанії (опціонально)
    location = models.ForeignKey(
        'directory.Location',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="counterparties_at_location",
        verbose_name="Юридична адреса компанії"
    )

    # Основні банківські реквізити для виставлення рахунків
    payment_details = models.ForeignKey(
        'directory.BankingDetail',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="counterparties_with_banking",
        verbose_name="Основні банківські реквізити"
    )

    # Головна контактна особа (директор, провідний логіст)
    primary_contact = models.ForeignKey(
        'directory.Contact',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="primary_for_counterparties",
        verbose_name="Головна контактна особа"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примітки"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Контрагент"
        verbose_name_plural = "Контрагенти"
        ordering = ["name"]

    def __str__(self):
        roles = []
        if self.is_client:
            roles.append("Клієнт")
        if self.is_carrier:
            roles.append("Перевізник")
        role_str = f" [{', '.join(roles)}]" if roles else ""
        return f"{self.name}{role_str}"