from django.contrib.admin.apps import AdminConfig


class DaaraAdminConfig(AdminConfig):
    """L'administration Django, avec le site de DAARA (apps/core/admin_site.py)."""

    default_site = "apps.core.admin_site.DaaraAdminSite"
