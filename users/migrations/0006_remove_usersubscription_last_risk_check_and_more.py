# Generated by Django 5.0.4 on 2025-03-29 04:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_usersubscription_last_risk_check_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersubscription',
            name='last_risk_check',
        ),
        migrations.RemoveField(
            model_name='usersubscription',
            name='risk_details',
        ),
        migrations.RemoveField(
            model_name='usersubscription',
            name='risk_level',
        ),
        migrations.RemoveField(
            model_name='usersubscription',
            name='risk_type',
        ),
    ]
