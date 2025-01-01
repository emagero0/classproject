 # test_runner.py

from django.test.runner import DiscoverRunner

class CustomTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        from django.conf import settings
        from django.contrib.auth import get_user_model
        # Ensure that our custom user model is used when testing
        if settings.AUTH_USER_MODEL != 'auth.User':
             settings.AUTH_USER_MODEL = get_user_model()._meta.label