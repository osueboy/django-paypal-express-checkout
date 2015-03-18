"""The models for the ``paypal_express_checkout`` app."""
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from paypal_express_checkout.constants import STATUS_CHOICES


class Item(models.Model):
    """
    Holds the information about an item, that is on Sale.

    The information will be needed to process the PayPal payment transaction.

    :identifier: A unique identifier for the item.
    :name: Name of the item.
    :description: Description of the item.
    :value: The price of the item.
    :currency: Short currency identifier. Defaults to USD.

    """
    identifier = models.CharField(
        max_length=256,
        verbose_name=_('Identifier'),
        blank=True,
    )

    name = models.CharField(
        max_length=2048,
        verbose_name=_('Name'),
    )

    description = models.CharField(
        max_length=4000,
        verbose_name=_('Description'),
    )

    value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_('Value'),
    )

    currency = models.CharField(
        max_length=16,
        default='USD',
    )

    def __unicode__(self):
        return '{0} - {1} {2}'.format(self.name, self.value, self.currency)


class PaymentTransaction(models.Model):
    """
    This model holds the information about a payment transaction.

    Needed in the process of the payment as well as later reference.

    :user: The user this transaction is related to.
    :creation_date: The date this transaction was created.
    :date: The date this transaction was saved last time.
    :transaction_id: The unique identifier of the transaction generated by
      PayPal.
    :value: The amount of the payment. Currency defaults to USD.
    :status: The status of the transaction.

    """
    user = models.ForeignKey(
        get_user_model(),
        verbose_name=_('User'),
    )

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True,
    )

    object_id = models.PositiveIntegerField(
        blank=True, null=True,
    )

    content_object = generic.GenericForeignKey(
        'content_type',
        'object_id',
    )

    creation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creation time'),
        blank=True, null=True,
    )

    date = models.DateTimeField(
        auto_now=True,
        auto_now_add=True,
        verbose_name=_('Time'),
    )

    transaction_id = models.CharField(
        max_length=32,
        verbose_name=_('Transaction ID'),
    )

    value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_('Transaction value'),
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        verbose_name=_('Payment status'),
    )

    class Meta:
        ordering = ['-creation_date', 'transaction_id', ]

    def __unicode__(self):
        return self.transaction_id


class PurchasedItem(models.Model):
    """
    Keeps track of which user purchased which items (and their quantities).

    This helps you to find out if and what your users have purchased.

    :user: FK to the user who made the purchase.
    :identifier: An identifier to select items of the same type. This can be
      helpful if you want to calculate the total shipping costs and the total
      cost of goods for a certain transaction.
    :transaction: The transaction that belongs to this purchase
    :content_object: Use this if you would like to point at any kind of item
      and not the Item model of this app.
    :item: The item that belongs to this purchase
    :price: The price of the item at the time of the purchase
    :quantity: The quantity of items that has been purchased

    """
    user = models.ForeignKey(
        get_user_model(),
        verbose_name=_('User'),
    )

    identifier = models.CharField(
        max_length=256,
        verbose_name=_('Identifier'),
        blank=True,
    )

    transaction = models.ForeignKey(
        PaymentTransaction,
        verbose_name=_('Transaction'),
    )

    item = models.ForeignKey(
        Item,
        verbose_name=_('Item'),
        null=True, blank=True,
    )

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True,
    )

    object_id = models.PositiveIntegerField(
        blank=True, null=True,
    )

    content_object = generic.GenericForeignKey(
        'content_type',
        'object_id',
    )

    price = models.FloatField(
        verbose_name=_('Price'),
        blank=True, null=True,
    )

    quantity = models.PositiveIntegerField(
        verbose_name=_('Quantity'),
    )

    class Meta:
        ordering = ['-transaction__date', 'transaction__transaction_id', ]

    def __unicode__(self):
        return '{0} {1} of {2} [{3}]'.format(
            self.quantity, self.item, self.user.email, self.transaction)


class PaymentTransactionError(models.Model):
    """
    A model to track errors during payment process.

    :data: When the error ocurred.
    :user: For which user the error occurred.
    :paypal_api_url: The API endpoint we have been calling, which has responded
      with the error.
    :request_data: The data payload we have been sending to the API endpoint.
    :response: The full response string from PayPal.
    :transaction: If we send a request at a point in time where we already have
      a transaction, we can add a FK to that transaction for easier cross
      referencing.

    """
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Time'),
    )

    user = models.ForeignKey(
        get_user_model(),
        verbose_name=_('User'),
    )

    paypal_api_url = models.CharField(
        max_length=4000,
        verbose_name=_('Paypal API URL'),
        blank=True,
    )

    request_data = models.TextField(
        verbose_name=_('Request data'),
        blank=True,
    )

    response = models.TextField(
        verbose_name=_('Response String'),
        blank=True,
    )

    transaction = models.ForeignKey(
        PaymentTransaction,
        blank=True, null=True,
        verbose_name=_('Payment transaction'),
    ),