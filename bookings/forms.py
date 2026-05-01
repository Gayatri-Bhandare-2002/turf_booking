from django import forms
from .models import Booking, Payment, SLOT_CHOICES, PAYMENT_METHOD_CHOICES
from datetime import date


class BookingForm(forms.ModelForm):
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': str(date.today())}),
        label='Booking Date'
    )
    slot = forms.ChoiceField(choices=SLOT_CHOICES, label='Time Slot')
    group_members = forms.IntegerField(min_value=1, max_value=22, label='Number of Group Members')
    age = forms.IntegerField(min_value=5, max_value=80, label='Your Age')

    class Meta:
        model = Booking
        fields = ['name', 'email', 'phone', 'age', 'group_members', 'booking_date', 'slot']
        widgets = {
            'name':  forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'placeholder': '10-digit Mobile Number', 'maxlength': '15'}),
        }

    def clean_booking_date(self):
        d = self.cleaned_data['booking_date']
        if d < date.today():
            raise forms.ValidationError("Booking date cannot be in the past.")
        return d

    def clean(self):
        cleaned = super().clean()
        booking_date = cleaned.get('booking_date')
        slot = cleaned.get('slot')
        if booking_date and slot:
            qs = Booking.objects.filter(booking_date=booking_date, slot=slot, status='confirmed')
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Slot {slot} on {booking_date} is already booked. Please choose another."
                )
        return cleaned


class PaymentForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        label='Payment Method'
    )
    upi_ref = forms.CharField(
        required=False,
        label='UPI / Transaction Reference Number',
        widget=forms.TextInput(attrs={'placeholder': 'Enter UPI Ref / Transaction ID'})
    )

    class Meta:
        model = Payment
        fields = ['payment_method', 'upi_ref']

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('payment_method')
        upi_ref = cleaned.get('upi_ref')
        if method in ('upi', 'card', 'netbanking') and not upi_ref:
            raise forms.ValidationError("Please enter your Transaction / UPI Reference Number.")
        return cleaned