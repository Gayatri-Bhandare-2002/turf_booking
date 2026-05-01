
import json
import csv
import calendar
from datetime import date, datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Q

from .models import Booking, Payment, SLOT_CHOICES, NIGHT_SLOTS, get_fee
from .forms import BookingForm


# ================= HOME PAGE =================
def index(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.status = 'pending'
            booking.save()
            return redirect('payment', booking_id=booking.booking_id)
    else:
        form = BookingForm()

    today = date.today()
    booked_slots_today = list(
        Booking.objects.filter(
            booking_date=today,
            status='confirmed'
        ).values_list('slot', flat=True)
    )

    return render(request, 'bookings/index.html', {
        'form': form,
        'booked_slots_today': booked_slots_today,
    })


# ================= SLOT FEE =================
def get_slot_fee(request):
    booking_date_str = request.GET.get('date')
    slot = request.GET.get('slot')

    if not booking_date_str or not slot:
        return JsonResponse({'error': 'Missing params'}, status=400)

    try:
        booking_date = datetime.strptime(
            booking_date_str,
            '%Y-%m-%d'
        ).date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date'}, status=400)

    weekday = booking_date.weekday()
    day_type = 'weekend' if weekday >= 5 else 'weekday'

    fee = get_fee(day_type, slot)

    is_booked = Booking.objects.filter(
        booking_date=booking_date,
        slot=slot,
        status='confirmed'
    ).exists()

    return JsonResponse({
        'fee': fee,
        'day_type': day_type,
        'time_period': 'night' if slot in NIGHT_SLOTS else 'day',
        'is_booked': is_booked,
    })


# ================= BOOKED SLOTS =================
def get_booked_slots(request):
    booking_date_str = request.GET.get('date')

    if not booking_date_str:
        return JsonResponse({'booked_slots': []})

    try:
        booking_date = datetime.strptime(
            booking_date_str,
            '%Y-%m-%d'
        ).date()
    except ValueError:
        return JsonResponse({'booked_slots': []})

    booked_slots = list(
        Booking.objects.filter(
            booking_date=booking_date,
            status='confirmed'
        ).values_list('slot', flat=True)
    )

    return JsonResponse({'booked_slots': booked_slots})


# ================= PAYMENT =================
def payment(request, booking_id):
    booking = get_object_or_404(
        Booking,
        booking_id=booking_id,
        status='pending'
    )

    if request.method == 'POST':
        Payment.objects.create(
            booking=booking,
            amount=booking.fee,
            payment_method='cash',
            transaction_id='MANUAL_' + booking.booking_id,
            status='completed',
            paid_at=timezone.now(),
        )

        booking.status = 'confirmed'
        booking.save()

        return redirect(
            'booking_success',
            booking_id=booking.booking_id
        )

    return render(request, 'bookings/payment.html', {
        'booking': booking,
        'amount': booking.fee,
    })


# ================= SUCCESS PAGE =================
def booking_success(request, booking_id):
    booking = get_object_or_404(
        Booking,
        booking_id=booking_id,
        status='confirmed'
    )

    payment_obj = getattr(booking, 'payment', None)

    booked_on_date = list(
        Booking.objects.filter(
            booking_date=booking.booking_date,
            status='confirmed'
        ).values_list('slot', flat=True)
    )

    slot_status = [
        {
            'value': s_val,
            'label': s_label,
            'is_booked': s_val in booked_on_date,
            'is_mine': s_val == booking.slot,
            'period': 'night' if s_val in NIGHT_SLOTS else 'day',
        }
        for s_val, s_label in SLOT_CHOICES
    ]

    return render(request, 'bookings/booking_success.html', {
        'booking': booking,
        'payment': payment_obj,
        'slot_status_json': json.dumps(slot_status),
    })


# ================= ADMIN LOGIN =================
def admin_login(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')

        messages.error(request, 'Invalid credentials or not an admin.')

    return render(request, 'bookings/admin_login.html')


# ================= ADMIN LOGOUT =================
def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# ================= CSV EXPORT =================
def make_csv_response(bookings_qs, filename):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )
    response.write('\ufeff')

    writer = csv.writer(response)

    writer.writerow([
        'Booking ID', 'Name', 'Email', 'Phone',
        'Booking Date', 'Slot', 'Fee',
        'Payment Status', 'Booking Status'
    ])

    for b in bookings_qs:
        pay = getattr(b, 'payment', None)

        writer.writerow([
            b.booking_id,
            b.name,
            b.email,
            b.phone,
            b.booking_date,
            b.get_slot_display_label(),
            b.fee,
            'Paid' if pay else 'No Payment',
            b.status,
        ])

    return response


# ================= MONTH EXPORT =================
@staff_member_required(login_url='/admin-login/')
def export_month(request):
    today = date.today()

    m = int(request.GET.get('month', today.month))
    y = int(request.GET.get('year', today.year))

    month_start = date(y, m, 1)
    month_end = date(
        y,
        m,
        calendar.monthrange(y, m)[1]
    )

    bookings_qs = Booking.objects.filter(
        booking_date__range=[month_start, month_end]
    )

    filename = (
        f'Bookings_{month_start.strftime("%B_%Y")}.csv'
    )

    return make_csv_response(bookings_qs, filename)


# ================= ADMIN DASHBOARD =================
@staff_member_required(login_url='/admin-login/')
def admin_dashboard(request):
    bookings = Booking.objects.all().order_by('-created_at')

    today = date.today()
    current_month = today.strftime('%B %Y')

    total = bookings.count()
    confirmed = bookings.filter(status='confirmed').count()
    pending = bookings.filter(status='pending').count()

    total_revenue = (
        bookings.filter(status='confirmed')
        .aggregate(total=Sum('fee'))['total'] or 0
    )

    today_booked = list(
        Booking.objects.filter(
            booking_date=today,
            status='confirmed'
        ).values_list('slot', flat=True)
    )

    bookings_list = []
    for b in bookings:
        payment = getattr(b, 'payment', None)

        bookings_list.append({
            'booking_id': b.booking_id,
            'name': b.name,
            'phone': b.phone,
            'email': b.email,
            'age': b.age,
            'group_members': b.group_members,
            'booking_date': b.booking_date.strftime('%d-%m-%Y'),
            'slot': b.get_slot_display_label(),
            'time_period': (
                'Night' if b.slot in NIGHT_SLOTS else 'Day'
            ),
            'fee': str(b.fee),
            'payment_status': (
                'Paid' if payment else 'No Payment'
            ),
            'pay_method': (
                payment.payment_method.title()
                if payment else '-'
            ),
            'txn_ref': (
                payment.transaction_id
                if payment else '-'
            ),
            'status': b.status,
            'created_at': b.created_at.strftime(
                '%d-%m-%Y %I:%M %p'
            ),
        })

    months_list = []
    for i in range(1, 13):
        months_list.append({
            'month': i,
            'year': today.year,
            'label': f'{calendar.month_name[i]} {today.year}'
        })

    context = {
        'bookings_json': json.dumps(bookings_list),
        'total': total,
        'confirmed': confirmed,
        'pending': pending,
        'total_revenue': total_revenue,
        'today': today,
        'today_booked': json.dumps(today_booked),
        'current_month': current_month,
        'months_list': months_list,
        'search': request.GET.get('search', ''),
        'date_filter': request.GET.get('date', ''),
    }

    return render(
        request,
        'bookings/admin_dashboard.html',
        context
    )

