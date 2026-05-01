from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=15)),
                ('age', models.PositiveIntegerField()),
                ('group_members', models.PositiveIntegerField()),
                ('booking_date', models.DateField()),
                ('slot', models.CharField(max_length=20, choices=[
                    ('12:00-13:00','12:00 PM – 1:00 PM'),('13:00-14:00','1:00 PM – 2:00 PM'),
                    ('14:00-15:00','2:00 PM – 3:00 PM'),('15:00-16:00','3:00 PM – 4:00 PM'),
                    ('16:00-17:00','4:00 PM – 5:00 PM'),('17:00-18:00','5:00 PM – 6:00 PM'),
                    ('18:00-19:00','6:00 PM – 7:00 PM'),('19:00-20:00','7:00 PM – 8:00 PM'),
                    ('20:00-21:00','8:00 PM – 9:00 PM'),('21:00-22:00','9:00 PM – 10:00 PM'),
                    ('22:00-23:00','10:00 PM – 11:00 PM'),('23:00-00:00','11:00 PM – 12:00 AM'),
                ])),
                ('day_type', models.CharField(max_length=10, blank=True, choices=[('weekday','Weekday (Mon-Fri)'),('weekend','Weekend (Sat-Sun)')])),
                ('time_period', models.CharField(max_length=10, blank=True, choices=[('day','Day Time'),('night','Night Time')])),
                ('fee', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(max_length=20, default='pending', choices=[('pending','Pending Payment'),('confirmed','Confirmed'),('cancelled','Cancelled')])),
                ('booking_id', models.CharField(max_length=20, unique=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='bookings.booking')),
                ('amount', models.PositiveIntegerField()),
                ('payment_method', models.CharField(max_length=20, choices=[('upi','UPI / GPay / PhonePe'),('card','Credit / Debit Card'),('netbanking','Net Banking'),('cash','Cash on Arrival')])),
                ('transaction_id', models.CharField(max_length=100, blank=True)),
                ('upi_ref', models.CharField(max_length=100, blank=True)),
                ('status', models.CharField(max_length=20, default='pending', choices=[('pending','Pending'),('completed','Completed'),('failed','Failed'),('refunded','Refunded')])),
                ('paid_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='booking',
            unique_together={('booking_date', 'slot')},
        ),
    ]