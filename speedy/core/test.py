import inspect

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase as DjangoTestCase
from django.test.runner import DiscoverRunner

from speedy.core.settings.utils import env


class SiteDiscoverRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        if not test_labels:
            test_labels = [label for label in settings.INSTALLED_APPS if label.startswith('speedy.')]
        return super().build_suite(test_labels, extra_tests, **kwargs)


def conditional_test(test_func):
    def wrapper(method_or_class):
        if inspect.isclass(method_or_class):
            # Decorate class
            if test_func():
                return method_or_class
            else:
                return
        else:
            # Decorate method
            def inner(*args, **kwargs):
                if test_func():
                    return method_or_class(*args, **kwargs)
                else:
                    return

            return inner

    return wrapper


class TestCase(DjangoTestCase):
    client_host = 'en.localhost'

    def _pre_setup(self):
        super()._pre_setup()
        self.client = self.client_class(HTTP_HOST=self.client_host)
        Site.objects.update(domain='localhost')


exclude_on_site = lambda site_id: conditional_test(lambda: int(settings.SITE_ID) != int(site_id))
exclude_on_speedy_net = exclude_on_site(env('SPEEDY_NET_SITE_ID'))
exclude_on_speedy_match = exclude_on_site(env('SPEEDY_MATCH_SITE_ID'))
exclude_on_speedy_composer = exclude_on_site(env('SPEEDY_COMPOSER_SITE_ID'))
exclude_on_speedy_mail_software = exclude_on_site(env('SPEEDY_MAIL_SOFTWARE_SITE_ID'))

# only_on_site = lambda site_id: conditional_test(lambda: int(settings.SITE_ID) == int(site_id))
# only_on_speedy_net = only_on_site(env('SPEEDY_NET_SITE_ID'))
# only_on_speedy_match = only_on_site(env('SPEEDY_MATCH_SITE_ID'))
