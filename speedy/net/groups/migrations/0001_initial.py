# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-13 17:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0026_auto_20161213_1857'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('entity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='accounts.Entity')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
            bases=('accounts.entity',),
        ),
    ]