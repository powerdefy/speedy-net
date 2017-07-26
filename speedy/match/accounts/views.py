from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, redirect
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext as _
from django.views import generic

from rules.contrib.views import LoginRequiredMixin

from speedy.core.base.views import FormValidMessageMixin
from speedy.core.accounts.views import IndexView as CoreIndexView
from speedy.core.accounts.views import ActivateSiteProfileView as CoreActivateSiteProfileView
from .forms import ProfilePrivacyForm


class IndexView(CoreIndexView):
    registered_redirect_to = 'matches:list'


class ActivateSiteProfileView(CoreActivateSiteProfileView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'gender_to_match' in self.request.POST:
            kwargs['data']['gender_to_match'] = ','.join(self.request.POST.getlist('gender_to_match'))
        return kwargs

    def get(self, request, *args, **kwargs):
        SPEEDY_NET_SITE_ID = settings.SITE_PROFILES['net']['site_id']
        if not request.user.is_active:
            return render(self.request, self.template_name, {'speedy_net_url': Site.objects.get(id=SPEEDY_NET_SITE_ID).domain})
        elif 'back' in request.GET:
            if request.user.profile.activation_step >= 1:
                request.user.profile.activation_step -= 1
                request.user.profile.save()
        elif 'step' in request.GET:
            if request.GET.get('step') == '-1':
                return redirect('accounts:edit_profile')
            step, errors = self.request.user.profile.validate_profile_and_activate()
            self.request.user.profile.activation_step = min(int(request.GET.get('step')), step)
            self.request.user.profile.save(update_fields={'activation_step'})
        else:
            step, errors = self.request.user.profile.validate_profile_and_activate()
            if (self.request.user.profile.activation_step == 0) and (
                step == len(settings.SITE_PROFILE_FORM_FIELDS)) and not self.request.user.has_confirmed_email():
                return redirect(reverse_lazy('accounts:edit_profile_credentials'))
        return super().get(self.request, *args, **kwargs)

    def get_account_activation_url(self):
        site = Site.objects.get_current()
        SPEEDY_MATCH_SITE_ID = settings.SITE_PROFILES['match']['site_id']
        if site.pk == SPEEDY_MATCH_SITE_ID:
            step = self.request.GET.get('step', self.request.user.profile.activation_step)
            return reverse_lazy('accounts:activate') + '?step=' + str(step)
        return reverse_lazy('accounts:activate')

    def form_valid(self, form):
        super().form_valid(form=form)
        site = Site.objects.get_current()
        if self.object.is_active:
            messages.success(self.request, pgettext_lazy(context=self.request.user.get_gender(), message='Welcome to {}!').format(_(site.name)))
        if self.request.user.profile.is_active:
            return redirect(to=reverse_lazy('matches:list'))
        else:
            return redirect(to=self.get_account_activation_url())



class EditProfilePrivacyView(LoginRequiredMixin, FormValidMessageMixin, generic.UpdateView):
    template_name = 'accounts/edit_profile/privacy.html'
    success_url = reverse_lazy('accounts:edit_profile_privacy')
    form_class = ProfilePrivacyForm

    def get_object(self, queryset=None):
        return self.request.user.profile

