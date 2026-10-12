from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm

from catalog.models import Practica

from .models import Membership, Rol

PERMISO = "catalog.change_practica"


@receiver(post_save, sender=Membership)
def otorgar_al_crear_membresia(sender, instance, **kwargs):
    if instance.rol != Rol.RESPONSABLE:
        return
    for practica in Practica.objects.filter(facultad=instance.facultad):
        assign_perm(PERMISO, instance.user, practica)


@receiver(post_delete, sender=Membership)
def retirar_al_borrar_membresia(sender, instance, **kwargs):
    if instance.rol != Rol.RESPONSABLE:
        return
    for practica in Practica.objects.filter(facultad=instance.facultad):
        remove_perm(PERMISO, instance.user, practica)


@receiver(post_save, sender=Practica)
def otorgar_en_practica_nueva(sender, instance, created, **kwargs):
    if not created:
        return
    miembros = Membership.objects.filter(facultad=instance.facultad, rol=Rol.RESPONSABLE).select_related("user")
    for membresia in miembros:
        assign_perm(PERMISO, membresia.user, instance)
