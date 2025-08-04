from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_user_groups(sender, **kwargs):
    # Importer ici pour éviter "Apps aren't loaded yet"
    from django.contrib.auth.models import Group, Permission

    groups_permissions = {
        'Administrateurs': ['add_employe', 'change_employe', 'delete_employe', 'view_employe'],
        'Éditeurs': ['add_employe', 'change_employe', 'delete_employe', 'view_employe'],
        'Lecteurs': ['view_employe'],
    }

    for group_name, perms in groups_permissions.items():
        group, created = Group.objects.get_or_create(name=group_name)
        permissions = Permission.objects.filter(codename__in=perms, content_type__app_label='personnel')
        group.permissions.set(permissions)

class PersonnelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personnel'

    def ready(self):
        post_migrate.connect(create_user_groups, sender=self)
