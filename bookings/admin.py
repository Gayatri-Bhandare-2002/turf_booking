from django.contrib import admin
from .models import Booking, Payment

class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ['paid_at', 'created_at']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display   = ['booking_id','name','email','phone','booking_date',
                      'slot','day_type','time_period','fee','status','created_at']
    list_filter    = ['status','day_type','time_period','booking_date']
    search_fields  = ['name','email','phone','booking_id']
    readonly_fields = ['booking_id','day_type','time_period','fee','created_at','updated_at']
    inlines        = [PaymentInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['booking','amount','payment_method','status','transaction_id','paid_at']
    list_filter   = ['status','payment_method']
    search_fields = ['booking__booking_id','booking__name','transaction_id']
    readonly_fields = ['paid_at','created_at']