from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from speedy.composer.accounts.models import SpeedyComposerNode


class ChordsTemplate(SpeedyComposerNode):

    class Meta:
        verbose_name = _('chords template')
        verbose_name_plural = _('chords templates')


class Accompaniment(SpeedyComposerNode):

    class Meta:
        verbose_name = _('accompaniment')
        verbose_name_plural = _('accompaniments')


class Folder(SpeedyComposerNode):
    user = models.ForeignKey(verbose_name=_('user'), to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')

    class Meta:
        verbose_name = _('folder')
        verbose_name_plural = _('folders')


class Composition(SpeedyComposerNode):
    folder = models.ForeignKey(verbose_name=_('folder'), to=Folder, on_delete=models.CASCADE, related_name='+')
    chords_template = models.ForeignKey(verbose_name=_('chords template'), to=ChordsTemplate, on_delete=models.CASCADE, related_name='+')
    accompaniment = models.ForeignKey(verbose_name=_('accompaniment'), to=Accompaniment, on_delete=models.CASCADE, related_name='+')
    tempo = models.SmallIntegerField(verbose_name=_('tempo'), default=105)
    public = models.BooleanField(verbose_name=_('public'), default=False)

    class Meta:
        verbose_name = _('composition')
        verbose_name_plural = _('compositions')


