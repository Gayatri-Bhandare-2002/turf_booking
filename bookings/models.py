from django.db import models
from django.utils import timezone

DAY_TYPE_CHOICES = [
    ('weekday', 'Weekday (Mon-Fri)'),
    ('weekend', 'Weekend (Sat-Sun)'),
]
TIME_PERIOD_CHOICES = [
    ('day', 'Day Time'),
    ('night', 'Night Time'),
]
PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
]
BOOKING_STATUS_CHOICES = [
    ('pending', 'Pending Payment'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
]
PAYMENT_METHOD_CHOICES = [
    ('upi', 'UPI / GPay / PhonePe'),
    ('card', 'Credit / Debit Card'),
    ('netbanking', 'Net Banking'),
    ('cash', 'Cash on Arrival'),
]
SLOT_CHOICES = [
    # DAY SLOTS (12 AM to 6 PM)
    ('00:00-01:00', '12:00 AM – 1:00 AM'),
    ('01:00-02:00', '1:00 AM – 2:00 AM'),
    ('02:00-03:00', '2:00 AM – 3:00 AM'),
    ('03:00-04:00', '3:00 AM – 4:00 AM'),
    ('04:00-05:00', '4:00 AM – 5:00 AM'),
    ('05:00-06:00', '5:00 AM – 6:00 AM'),
    ('06:00-07:00', '6:00 AM – 7:00 AM'),
    ('07:00-08:00', '7:00 AM – 8:00 AM'),
    ('08:00-09:00', '8:00 AM – 9:00 AM'),
    ('09:00-10:00', '9:00 AM – 10:00 AM'),
    ('10:00-11:00', '10:00 AM – 11:00 AM'),
    ('11:00-12:00', '11:00 AM – 12:00 PM'),
    ('12:00-13:00', '12:00 PM – 1:00 PM'),
    ('13:00-14:00', '1:00 PM – 2:00 PM'),
    ('14:00-15:00', '2:00 PM – 3:00 PM'),
    ('15:00-16:00', '3:00 PM – 4:00 PM'),
    ('16:00-17:00', '4:00 PM – 5:00 PM'),
    ('17:00-18:00', '5:00 PM – 6:00 PM'),
    # NIGHT SLOTS (6 PM to 12 AM)
    ('18:00-19:00', '6:00 PM – 7:00 PM'),
    ('19:00-20:00', '7:00 PM – 8:00 PM'),
    ('20:00-21:00', '8:00 PM – 9:00 PM'),
    ('21:00-22:00', '9:00 PM – 10:00 PM'),
    ('22:00-23:00', '10:00 PM – 11:00 PM'),
    ('23:00-00:00', '11:00 PM – 12:00 AM'),
]

NIGHT_SLOTS = [
    '18:00-19:00', '19:00-20:00', '20:00-21:00',
    '21:00-22:00', '22:00-23:00', '23:00-00:00',
]
FEES = {
    'weekday_day': 700,
    'weekday_night': 900,
    'weekend_day': 900,
    'weekend_night': 1100,
}

def get_fee(day_type, slot):
    period = 'night' if slot in NIGHT_SLOTS else 'day'
    return FEES.get(f'{day_type}_{period}', 700)


class Booking(models.Model):
    name          = models.CharField(max_length=100)
    email         = models.EmailField()
    phone         = models.CharField(max_length=15)
    age           = models.PositiveIntegerField()
    group_members = models.PositiveIntegerField(help_text='Number of members in group')

    booking_date  = models.DateField()
    slot          = models.CharField(max_length=20, choices=SLOT_CHOICES)
    day_type      = models.CharField(max_length=10, choices=DAY_TYPE_CHOICES, blank=True)
    time_period   = models.CharField(max_length=10, choices=TIME_PERIOD_CHOICES, blank=True)
    fee           = models.PositiveIntegerField(default=0)

    status        = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending')
    booking_id    = models.CharField(max_length=20, unique=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['booking_date', 'slot']]

    def save(self, *args, **kwargs):
        if self.booking_date:
            weekday = self.booking_date.weekday()
            self.day_type = 'weekend' if weekday >= 5 else 'weekday'
        self.time_period = 'night' if self.slot in NIGHT_SLOTS else 'day'
        self.fee = get_fee(self.day_type, self.slot)
        if not self.booking_id:
            import random, string
            self.booking_id = 'TRF' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_id} - {self.name} | {self.booking_date} | {self.slot}"

    def get_slot_display_label(self):
        for value, label in SLOT_CHOICES:
            if value == self.slot:
                return label
        return self.slot


class Payment(models.Model):
    booking        = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount         = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True)
    upi_ref        = models.CharField(max_length=100, blank=True)
    status         = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    paid_at        = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.booking.booking_id} ₹{self.amount} [{self.status}]"

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.paid_at:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)