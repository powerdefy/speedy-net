# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-10 18:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('im', '0003_read_mark'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chat',
            options={'ordering': ('-last_message__date_created', '-date_updated'), 'verbose_name': 'chat', 'verbose_name_plural': 'chat'},
        ),
        migrations.AlterModelOptions(
            name='readmark',
            options={'get_latest_by': 'date_created', 'verbose_name': 'read mark', 'verbose_name_plural': 'read marks'},
        ),
    ]
