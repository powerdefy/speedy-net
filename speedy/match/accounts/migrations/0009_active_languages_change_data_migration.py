# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-04 12:26
from __future__ import unicode_literals

from django.db import migrations


def forwards_func(apps, schema_editor):
    from speedy.core.accounts.models import User
    SpeedyMatchSiteProfile = apps.get_model("match_accounts", "SiteProfile")
    for speedy_match_profile in SpeedyMatchSiteProfile.objects.all():
        speedy_match_profile.active_languages_1 = list(filter(None, (l.strip() for l in speedy_match_profile.active_languages.split(','))))
        speedy_match_profile.save()
        print (speedy_match_profile.pk, speedy_match_profile.active_languages, speedy_match_profile.active_languages_1)


def backwards_func(apps, schema_editor):
    SpeedyMatchSiteProfile = apps.get_model("match_accounts", "SiteProfile")
    for speedy_match_profile in SpeedyMatchSiteProfile.objects.all():
        print (speedy_match_profile.pk, speedy_match_profile.active_languages, speedy_match_profile.active_languages_1)


class Migration(migrations.Migration):

    dependencies = [
        ('match_accounts', '0008_siteprofile_active_languages_1'),
    ]

    operations = [
        migrations.RunPython(forwards_func, backwards_func),
    ]
