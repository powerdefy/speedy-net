# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-13 14:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0024_user_diet'),
    ]

    operations = [
        migrations.CreateModel(
            name='NamedEntity',
            fields=[
                ('entity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='accounts.Entity')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
            bases=('accounts.entity',),
        ),
        migrations.AlterField(
            model_name='user',
            name='diet',
            field=models.SmallIntegerField(choices=[(0, 'Please select...'), (1, 'Vegan (eats only plants and fungi)'), (2, "Vegetarian (doesn't eat fish and meat)"), (3, 'Carnist (eats animals)')], default=0, verbose_name='diet'),
        ),
    ]