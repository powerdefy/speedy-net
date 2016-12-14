from crispy_forms.bootstrap import InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Div, HTML, Row, Hidden, Layout
from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from speedy.core.forms import ModelFormWithDefaults
from speedy.core.mail import send_mail
from .models import User, UserEmailAddress, SiteProfile, normalize_username
from .utils import get_site_profile_model

DATE_FIELD_FORMATS = [
    '%Y-%m-%d',  # '2006-10-25'
    '%m/%d/%Y',  # '10/25/2006'
    '%m/%d/%y',  # '10/25/06'
    '%b %d %Y',  # 'Oct 25 2006'
    '%b %d, %Y',  # 'Oct 25, 2006'
    '%d %b %Y',  # '25 Oct 2006'
    '%d %b, %Y',  # '25 Oct, 2006'
    '%B %d %Y',  # 'October 25 2006'
    '%B %d, %Y',  # 'October 25, 2006'
    '%d %B %Y',  # '25 October 2006'
    '%d %B, %Y',  # '25 October, 2006'
]

DEFAULT_DATE_FIELD_FORMAT = '%B %d, %Y'


class CleanEmailMixin(object):
    def clean_email(self):
        email = self.cleaned_data['email']
        email = User.objects.normalize_email(email)
        email = email.lower()
        if UserEmailAddress.objects.filter(email=email).exists():
            # If this email address is not confirmed, delete it. Maybe another user added it but it belongs to the current user.
            UserEmailAddress.objects.filter(email=email, is_confirmed=False).delete()
            # If this email address is confirmed, raise an exception.
            if UserEmailAddress.objects.filter(email=email).exists():
                raise forms.ValidationError(_('This email is already in use.'))
        return email


class CleanNewPasswordMixin(object):
    def clean_new_password1(self):
        password = self.cleaned_data['new_password1']
        if len(password) < User.MIN_PASSWORD_LENGTH:
            raise forms.ValidationError(_('Password too short.'))
        if len(password) > User.MAX_PASSWORD_LENGTH:
            raise forms.ValidationError(_('Password too long.'))
        return password


class LocalizedFirstLastNameMixin(object):
    def __init__(self, *args, **kwargs):
        self.language = kwargs.pop('language', 'en')
        super().__init__(*args, **kwargs)
        for loc_field in reversed(self.get_localized_fields()):
            self.fields[loc_field] = User._meta.get_field(loc_field).formfield()
            self.fields[loc_field].required = True
            self.fields.move_to_end(loc_field, last=False)
            self.initial[loc_field] = getattr(self.instance, loc_field, '')

    def save(self, commit=True):
        instance = super().save(commit=False)
        for loc_field in self.get_localized_fields():
            setattr(instance, loc_field, self.cleaned_data[loc_field])
        if commit:
            instance.save()
        return instance

    def get_localized_fields(self):
        loc_fields = ('first_name', 'last_name')
        return ['{}_{}'.format(loc_field, self.language) for loc_field in loc_fields]


class RegistrationForm(CleanEmailMixin, CleanNewPasswordMixin, LocalizedFirstLastNameMixin, forms.ModelForm):
    email = forms.EmailField(label=_('Your email'))
    new_password1 = forms.CharField(label=_("New password"), strip=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'slug', 'new_password1', 'gender', 'date_of_birth')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].label = _('New username')
        self.fields['date_of_birth'].input_formats = DATE_FIELD_FORMATS
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Create an account')))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["new_password1"])
        if commit:
            user.save()
            email_address = user.email_addresses.create(
                email=self.cleaned_data['email'],
                is_confirmed=False,
                is_primary=True,
            )
        return user


class ProfileForm(LocalizedFirstLastNameMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('date_of_birth', 'photo', 'slug', 'gender')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['date_of_birth'].input_formats = DATE_FIELD_FORMATS
        self.fields['date_of_birth'].widget.format = DEFAULT_DATE_FIELD_FORMAT
        self.helper = FormHelper()
        # split into two columns
        field_names = list(self.fields.keys())
        self.helper.add_layout(Div(*[
            Row(*[
                Div(field, css_class='col-md-6')
                for field in pair])
            for pair in zip(field_names[::2], field_names[1::2])
            ]))
        self.helper.add_input(Submit('submit', _('Save Changes')))

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        username = self.instance.username
        if normalize_username(slug=slug) != username:
            raise forms.ValidationError(_('You can\'t change your username'))
        return slug


class ProfilePrivacyForm(forms.ModelForm):
    class Meta:
        model = SiteProfile
        fields = ('access_dob_day_month', 'access_dob_year')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Save Changes')))


class ProfileNotificationsForm(forms.ModelForm):
    class Meta:
        model = get_site_profile_model()
        fields = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for field in self._meta.model._meta.fields:
            if field.name.startswith('notify_'):
                self.fields[field.name] = field.formfield()
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Save Changes')))

    def save(self, commit=True):
        for field_name in self.fields.keys():
            setattr(self.instance, field_name, self.cleaned_data[field_name])
        return super().save(commit=commit)


class LoginForm(auth_forms.AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = self.data.copy()
        if 'username' in self.data:
            self.data['username'] = self.data['username'].lower()
        self.fields['username'].label = _('Username or email')
        self.helper = FormHelper()
        self.helper.add_layout(Div(
            'username',
            'password',
            Submit('submit', _('Login')),
            HTML('<a class="btn btn-link" href="{link}">{text}</a>'.format(
                link=reverse('accounts:password_reset'),
                text=_('Forgot password?'),
            )),
        ))

    def confirm_login_allowed(self, user):
        return None


class PasswordResetForm(auth_forms.PasswordResetForm):
    @property
    def helper(self):
        helper = FormHelper()
        helper.add_input(Submit('submit', _('Submit')))
        return helper

    def get_users(self, email):
        email_addresses = UserEmailAddress.objects.select_related('user').filter(email__iexact=email,
                                                                                 user__is_active=True)
        return {e.user for e in email_addresses if e.user.has_usable_password()}

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        send_mail([to_email], 'accounts/email/password_reset', context)


class SetPasswordForm(CleanNewPasswordMixin, auth_forms.SetPasswordForm):
    @property
    def helper(self):
        helper = FormHelper()
        helper.add_input(Submit('submit', _('Submit')))
        return helper


class PasswordChangeForm(CleanNewPasswordMixin, auth_forms.PasswordChangeForm):
    def __init__(self, **kwargs):
        user = kwargs.pop('user')
        super().__init__(user, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Hidden('_form', 'password'))
        self.helper.add_input(Submit('submit', _('Change')))


class SiteProfileActivationForm(forms.ModelForm):
    class Meta:
        model = get_site_profile_model()
        fields = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        site = Site.objects.get_current()
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Activate my {} account').format(site.name)))

    def save(self, commit=True):
        if commit:
            self.instance.activate()
        return super().save(commit=commit)


class SiteProfileDeactivationForm(forms.Form):
    password = forms.CharField(label=_('Your password'), strip=False, widget=forms.PasswordInput)

    def __init__(self, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(**kwargs)
        site = Site.objects.get_current()
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Deactivate your {} account').format(site.name), css_class='btn-danger'))

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.user.check_password(password):
            raise forms.ValidationError(_('Invalid password'))
        return password


class UserEmailAddressForm(CleanEmailMixin, ModelFormWithDefaults):
    class Meta:
        model = UserEmailAddress
        fields = ('email',)

    @property
    def helper(self):
        helper = FormHelper()
        helper.add_input(Submit('submit', _('Add')))
        return helper


class UserEmailAddressPrivacyForm(ModelFormWithDefaults):
    class Meta:
        model = UserEmailAddress
        fields = ('access',)

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.form_action = reverse('accounts:change_email_privacy', kwargs={'pk': self.instance.id})
        helper.field_template = 'bootstrap3/layout/inline_field.html'
        helper.layout = Layout(
            InlineField('access', css_class='input-sm'),
        )
        return helper
