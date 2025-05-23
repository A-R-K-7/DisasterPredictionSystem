# Generated by Django 5.0.4 on 2025-03-27 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_usersubscription_latitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersubscription',
            name='last_risk_check',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='risk_details',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='risk_level',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='risk_type',
            field=models.CharField(blank=True, choices=[('earthquake', 'Earthquake'), ('cyclone', 'Cyclone')], max_length=20),
        ),
    ]
