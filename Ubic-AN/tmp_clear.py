from inventory.models import Activo
deleted, _ = Activo.objects.all().delete()
print(f"{deleted} activos borrados OK")
