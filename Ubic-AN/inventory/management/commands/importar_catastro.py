import csv
from django.core.management.base import BaseCommand
from inventory.models import Activo


class Command(BaseCommand):
    help = 'Importa el catastro de equipos TI desde un archivo CSV (separador ;)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo CSV con el catastro')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']

        def clean(val):
            """Devuelve None si la celda está vacía, NA o solo espacios."""
            val = (val or '').strip()
            if val.upper() in ('', 'NA', 'N/A', 'NONE', '.'):
                return None
            return val

        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')

                created_count = 0
                updated_count = 0

                for row in reader:
                    numero_serie = clean(row.get('N. SERIE', ''))

                    # Saltamos filas sin número de serie (ej: la última línea con solo '.')
                    if not numero_serie:
                        continue

                    datos = {
                        'ant_centro':       clean(row.get('ANT. CENTRO', '')),
                        'etiqueta':         clean(row.get('ETIQUETA', '')) or clean(row.get('ANT. CENTRO', '')), # Map ANT. CENTRO as default label if ETIQUETA doesn't exist
                        'proveedor':        clean(row.get('PROVEEDOR', '')),
                        'ubicacion_texto':  clean(row.get('UBICACIÓN', '')),
                        'usuario':          clean(row.get('USUARIO', '')),
                        'marca':            clean(row.get('MARCA', '')),
                        'modelo':           clean(row.get('MODELO', '')),
                        'cpu':              clean(row.get('CPU', '')),
                        'ram':              clean(row.get('RAM/TIPO', '')),
                        'almacenamiento':   clean(row.get('ALMACENAMIENTO/TIPO', '')),
                        'ip':               clean(row.get('IP/RED WIFI', '')),
                        'contrasena_wifi':  clean(row.get('CONTRASEÑA WIFI', '')),
                        'anydesk':          clean(row.get('ID ANYDESK', '')),
                        'pass_anydesk':     clean(row.get('PASS ANY', '')),
                        'version_win':      clean(row.get('VERSION WIN', '')),
                        'licencia_office':  clean(row.get('LICENCIA OFFICE', '')),
                        'pass_office':      clean(row.get('PASS OFFICE', '')),
                        'key_office':       clean(row.get('KEY LICENCIA OFFICE', '')),
                        'fecha_instalacion': clean(row.get('FECHA INSTALACION', '')),
                        'comentarios':      clean(row.get('COMENTARIOS', '')),
                        'mac_managerlab':   clean(row.get('MAC MANAGERLAB', '')),
                        'pass_managerlab':  clean(row.get('PASS MANAGERLAB', '')),
                    }

                    activo, created = Activo.objects.update_or_create(
                        numero_serie=numero_serie,
                        defaults=datos
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                self.stdout.write(self.style.SUCCESS(
                    f'Importación completada. {created_count} activos nuevos, {updated_count} actualizados.'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'El archivo {csv_file_path} no fue encontrado.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocurrió un error: {e}'))
