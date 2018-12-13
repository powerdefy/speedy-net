from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from speedy.core.mail import mail_managers
from speedy.core.models import TimeStampedModel


class Feedback(TimeStampedModel):
    TYPE_FEEDBACK = 0
    TYPE_REPORT_ENTITY = 1
    TYPE_REPORT_FILE = 2
    TYPE_CHOICES = (
        (TYPE_FEEDBACK, _('Feedback')),
        (TYPE_REPORT_ENTITY, _('Abuse (User)')),
        (TYPE_REPORT_FILE, _('Abuse (Photo)')),
    )

    sender = models.ForeignKey(verbose_name=_('sender'), to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sender_name = models.CharField(verbose_name=_('your name'), max_length=255, blank=True)
    sender_email = models.EmailField(verbose_name=_('your email'), blank=True)
    type = models.PositiveIntegerField(verbose_name=_('type'), choices=TYPE_CHOICES)
    text = models.TextField(verbose_name=_('your message'))
    report_entity = models.ForeignKey(verbose_name=_('reported entity'), to='accounts.Entity', on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    report_file = models.ForeignKey(verbose_name=_('reported photo'), to='uploads.File', on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')

    class Meta:
        verbose_name = _('feedback')
        verbose_name_plural = _('feedbacks')
        ordering = ('-date_created',)

    def __str__(self):
        if self.type == self.TYPE_REPORT_ENTITY:
            on = ' on {}'.format(self.report_entity.user)
        elif self.type == self.TYPE_REPORT_FILE:
            on = ' on {}'.format(self.report_file)
        else:
            on = ''
        if self.sender:
            by = str(self.sender)
        else:
            by = self.sender_name
        return '{}{} by {}'.format(self.get_type_display(), on, by)


@receiver(models.signals.post_save, sender=Feedback)
def email_feedback(sender, instance: Feedback, created: bool, **kwargs):
    if created:
        mail_managers('feedback/email/admin_feedback',
                      {'feedback': instance},
                      headers={'Reply-To': instance.sender_email or instance.sender.email})