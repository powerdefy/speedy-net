# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-03 13:45
from __future__ import unicode_literals

from django.db import migrations
import speedy.net.accounts.managers


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20161103_1015'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', speedy.net.accounts.managers.UserManager()),
            ],
        ),
    ]