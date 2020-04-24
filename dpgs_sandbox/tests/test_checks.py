from django.apps import apps
from django.conf import settings
from django.core import checks
from django.test import TestCase, override_settings

from django_pgschemas.checks import check_principal_apps, check_other_apps, get_user_app


BASE_PUBLIC = {"TENANT_MODEL": "shared_public.Tenant", "DOMAIN_MODEL": "shared_public.DOMAIN"}


class AppConfigTestCase(TestCase):
    """
    Tests TENANTS settings is properly defined.
    """

    def setUp(self):
        self.app_config = apps.get_app_config("django_pgschemas")

    def test_core_apps_location(self):
        with override_settings(TENANTS={"public": {"APPS": [], **BASE_PUBLIC}}):
            errors = check_principal_apps(self.app_config)
            expected_errors = [
                checks.Error("Your tenant app 'shared_public' must be on the 'public' schema.", id="pgschemas.W001"),
                checks.Error("Your domain app 'shared_public' must be on the 'public' schema.", id="pgschemas.W001"),
            ]
            self.assertEqual(errors, expected_errors)
        with override_settings(
            TENANTS={"public": {"APPS": ["shared_public"], **BASE_PUBLIC}, "default": {"APPS": ["shared_public"]}}
        ):
            errors = check_principal_apps(self.app_config)
            expected_errors = [
                checks.Error(
                    "Your tenant app 'shared_public' in TENANTS['default']['APPS'] must be on the 'public' schema only.",
                    id="pgschemas.W001",
                ),
                checks.Error(
                    "Your domain app 'shared_public' in TENANTS['default']['APPS'] must be on the 'public' schema only.",
                    id="pgschemas.W001",
                ),
            ]
            self.assertEqual(errors, expected_errors)

    def test_contenttypes_location(self):
        with override_settings(TENANTS={"default": {"APPS": ["django.contrib.contenttypes"]}}):
            errors = check_other_apps(self.app_config)
            expected_errors = [
                checks.Warning(
                    "'django.contrib.contenttypes' in TENANTS['default']['APPS'] must be on 'public' schema only.",
                    id="pgschemas.W002",
                )
            ]
            self.assertEqual(errors, expected_errors)
        with override_settings(TENANTS={"default": {}, "www": {"APPS": ["django.contrib.contenttypes"]}}):
            errors = check_other_apps(self.app_config)
            expected_errors = [
                checks.Warning(
                    "'django.contrib.contenttypes' in TENANTS['www']['APPS'] must be on 'public' schema only.",
                    id="pgschemas.W002",
                )
            ]
            self.assertEqual(errors, expected_errors)

    def test_user_session_location(self):
        user_app = get_user_app()

        with override_settings(TENANTS={"default": {"APPS": ["django.contrib.sessions"]}}):
            errors = check_other_apps(self.app_config)
            expected_errors = [
                checks.Warning(
                    "'%s' must be together with '%s' in TENANTS['%s']['APPS']."
                    % (user_app, "django.contrib.sessions", "default"),
                    id="pgschemas.W003",
                )
            ]
            self.assertEqual(errors, expected_errors)
        with override_settings(
            TENANTS={
                "default": {"APPS": ["shared_common"]},
                "www": {"APPS": ["shared_common", "django.contrib.sessions"]},
            }
        ):
            errors = check_other_apps(self.app_config)
            expected_errors = [
                checks.Warning(
                    "'%s' must be together with '%s' in TENANTS['%s']['APPS']."
                    % ("django.contrib.sessions", user_app, "default"),
                    id="pgschemas.W003",
                )
            ]
            self.assertEqual(errors, expected_errors)