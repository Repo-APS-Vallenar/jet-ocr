from django.contrib.gis.db import models

class Recinto(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class Plano(models.Model):
    recinto = models.ForeignKey(Recinto, on_delete=models.CASCADE, related_name='planos')
    nombre = models.CharField(max_length=255, help_text="e.g. Piso 1")
    nivel = models.IntegerField(default=1, help_text="Floor level number")
    imagen = models.ImageField(upload_to='planos/')

    def __str__(self):
        return f"{self.recinto.nombre} - {self.nombre}"

class Activo(models.Model):
    # Datos del CSV
    ant_centro    = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ant. Centro")
    etiqueta      = models.CharField(max_length=255, blank=True, null=True, verbose_name="Etiqueta")
    proveedor     = models.CharField(max_length=255, blank=True, null=True, verbose_name="Proveedor")
    ubicacion_texto = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ubicación (CSV)")
    usuario       = models.CharField(max_length=255, blank=True, null=True, verbose_name="Usuario")
    marca         = models.CharField(max_length=255, blank=True, null=True, verbose_name="Marca")
    modelo        = models.CharField(max_length=255, blank=True, null=True, verbose_name="Modelo")
    numero_serie  = models.CharField(max_length=255, blank=True, null=True, verbose_name="N° Serie")
    cpu           = models.CharField(max_length=255, blank=True, null=True, verbose_name="CPU")
    ram           = models.CharField(max_length=255, blank=True, null=True, verbose_name="RAM/Tipo")
    almacenamiento = models.CharField(max_length=255, blank=True, null=True, verbose_name="Almacenamiento/Tipo")
    ip            = models.CharField(max_length=255, blank=True, null=True, verbose_name="IP/Red WiFi")
    contrasena_wifi = models.CharField(max_length=255, blank=True, null=True, verbose_name="Contraseña WiFi")
    anydesk       = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID AnyDesk")
    pass_anydesk  = models.CharField(max_length=255, blank=True, null=True, verbose_name="Pass AnyDesk")
    version_win   = models.CharField(max_length=255, blank=True, null=True, verbose_name="Versión Windows")
    licencia_office = models.CharField(max_length=255, blank=True, null=True, verbose_name="Licencia Office")
    pass_office   = models.CharField(max_length=255, blank=True, null=True, verbose_name="Pass Office")
    key_office    = models.CharField(max_length=255, blank=True, null=True, verbose_name="Key Licencia Office")
    fecha_instalacion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fecha Instalación")
    comentarios   = models.TextField(blank=True, null=True, verbose_name="Comentarios")
    mac_managerlab = models.CharField(max_length=255, blank=True, null=True, verbose_name="MAC ManagerLab")
    pass_managerlab = models.CharField(max_length=255, blank=True, null=True, verbose_name="Pass ManagerLab")

    # Campos de ubicación en plano
    plano   = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, blank=True, related_name='activos', verbose_name="Plano")
    coord_x = models.FloatField(null=True, blank=True, verbose_name="Coord X", help_text="Coordenada X en la imagen (CRS.Simple)")
    coord_y = models.FloatField(null=True, blank=True, verbose_name="Coord Y", help_text="Coordenada Y en la imagen (CRS.Simple)")

    class Meta:
        verbose_name = "Activo"
        verbose_name_plural = "Activos"

    def __str__(self):
        return f"{self.ip or '(sin IP)'} – {self.usuario or '(sin usuario)'} – {self.marca or ''} {self.modelo or ''}"

