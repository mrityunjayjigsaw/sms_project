# transactions/signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from .models import Transaction, SchoolTransactionCounter

@receiver(pre_save, sender=Transaction)
def generate_school_transaction_id(sender, instance, **kwargs):
    if not instance.transaction_id:
        with db_transaction.atomic():
            counter, created = SchoolTransactionCounter.objects.select_for_update().get_or_create(school=instance.school)
            counter.last_number += 1
            counter.save()

            txn_number = counter.last_number
            school_code = instance.school.short_name.upper() if instance.school.short_name else "SCH"

            instance.transaction_id = f"{school_code}-TXN{txn_number:08d}"
