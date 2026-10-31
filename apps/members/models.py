from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Compte de connexion.

    Défini dès la phase 0 : un modèle d'utilisateur personnalisé ne peut plus être introduit
    après la première migration. Rôles cumulables et profil de membre arrivent en phase 1.
    """
