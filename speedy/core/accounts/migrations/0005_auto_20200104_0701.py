# Generated by Django 2.1.15 on 2020-01-04 05:01

from django.db import migrations


def forwards_func(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.all():
        user.has_confirmed_email = user.email_addresses.filter(is_confirmed=True).exists()
        user.save()


def backwards_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_has_confirmed_email'),
    ]

    operations = [
        migrations.RunPython(forwards_func, backwards_func),
    ]


