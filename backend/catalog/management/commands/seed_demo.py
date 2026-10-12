import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Membership
from catalog import seed_data as datos
from catalog.models import ODS, Facultad, Origen, Practica, Region
from evidence.models import Evidencia, TipoEvidencia
from indicators.models import EstadoMedicion, Indicador, Medicion


class Command(BaseCommand):
    help = (
        "Carga regiones, facultades y ODS. Sin --solo-catalogos también crea usuarios de demo "
        "(contraseña en SUSI_DEMO_PASSWORD) y prácticas ilustrativas."
    )

    def add_arguments(self, parser):
        parser.add_argument("--solo-catalogos", action="store_true", help="No crea usuarios ni prácticas.")

    def handle(self, *args, **opciones):
        solo_catalogos = opciones["solo_catalogos"]
        password = os.environ.get("SUSI_DEMO_PASSWORD", "")
        if not solo_catalogos and not password:
            raise CommandError(
                "Definí SUSI_DEMO_PASSWORD (contraseña de los usuarios de demo) o usá --solo-catalogos."
            )
        with transaction.atomic():
            self._cargar_catalogos()
            if not solo_catalogos:
                usuarios = self._cargar_usuarios(password)
                self._cargar_practicas(usuarios)
        self.stdout.write(self.style.SUCCESS("Datos de demo cargados."))

    def _cargar_catalogos(self):
        for nombre_region, facultades in datos.FACULTADES.items():
            region, _ = Region.objects.get_or_create(nombre=nombre_region)
            for nombre in facultades:
                Facultad.objects.get_or_create(
                    nombre=nombre,
                    defaults={"region": region, "es_nivel_central": nombre_region == "Nivel Central"},
                )
        for numero, nombre in datos.ODS.items():
            ODS.objects.get_or_create(numero=numero, defaults={"nombre": nombre})

    def _cargar_usuarios(self, password: str) -> dict:
        User = get_user_model()
        usuarios = {}
        facultades = Facultad.objects.filter(nombre__in=datos.FACULTADES_DEMO)
        for definicion in datos.USUARIOS_DEMO:
            username = definicion["username"]
            usuario = User.objects.filter(username=username).first()
            if usuario is None:
                if definicion["admin"]:
                    usuario = User.objects.create_superuser(username=username, password=password)
                else:
                    usuario = User.objects.create_user(username=username, password=password)
                self.stdout.write(f"Usuario creado: {username}")
            if definicion["rol"]:
                for facultad in facultades:
                    Membership.objects.get_or_create(user=usuario, facultad=facultad, rol=definicion["rol"])
            usuarios[username] = usuario
        return usuarios

    def _cargar_practicas(self, usuarios: dict):
        responsable = usuarios["responsable.demo"]
        validador = usuarios["validador.demo"]
        for entrada in datos.PRACTICAS_DEMO:
            facultad = Facultad.objects.get(nombre=entrada["facultad"])
            if Practica.objects.filter(facultad=facultad, nombre=entrada["nombre"]).exists():
                continue
            practica = Practica.objects.create(
                facultad=facultad,
                nombre=entrada["nombre"],
                dimension=entrada["dimension"],
                estado=entrada["estado"],
                proposito=entrada["proposito"],
                responsable=responsable if entrada["responsable"] else None,
                origen=Origen.ILUSTRATIVA,
            )
            practica.ods.set(ODS.objects.filter(numero__in=entrada["ods"]))
            if entrada["indicador"]:
                indicador = Indicador.objects.create(practica=practica, **entrada["indicador"])
                for periodo, valor, estado in entrada["mediciones"]:
                    self._crear_medicion(indicador, periodo, valor, estado, responsable, validador)

    @staticmethod
    def _crear_medicion(indicador, periodo, valor, estado, responsable, validador):
        validada = estado == EstadoMedicion.VALIDADA
        medicion = Medicion.objects.create(
            indicador=indicador,
            periodo=periodo,
            valor=valor,
            estado=estado,
            cargado_por=responsable,
            validado_por=validador if validada else None,
            validado_en=timezone.now() if validada else None,
            comentario_validacion="Conforme (dato ilustrativo)" if validada else "",
        )
        Evidencia.objects.create(
            medicion=medicion,
            tipo=TipoEvidencia.ENLACE,
            url=datos.URL_EVIDENCIA_ILUSTRATIVA,
            descripcion="Evidencia ilustrativa",
            creado_por=responsable,
        )
