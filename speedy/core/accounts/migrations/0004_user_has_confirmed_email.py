# Generated by Django 2.1.15 on 2020-01-04 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20191031_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_confirmed_email',
            field=models.BooleanField(default=False),
        ),
    ]
