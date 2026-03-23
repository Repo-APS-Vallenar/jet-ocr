# Ubic-AN: Gestión de Inventario TI

Aplicación web local desarrollada en Django + PostGIS para gestionar visualmente equipos TI sobre planos arquitectónicos usando Leaflet.js.

## Prerrequisitos
- Docker y Docker Compose instalados.

## Instrucciones de Despliegue Local (Red CESFAM)

1. **Clonar o copiar** esta carpeta generada `Ubic-AN` en el servidor o equipo local.
2. Abre una terminal y navega hasta la carpeta del proyecto.
3. **Levanta los contenedores**:
   ```bash
   docker-compose up -d --build
   ```
4. **Ejecuta las migraciones de Base de Datos** (solo la primera vez o cuando haya cambios en los modelos):
   ```bash
   docker-compose run --rm web python manage.py migrate
   ```
5. **Crea un superusuario** (para acceder al panel de administración y cargar las imágenes de los planos):
   ```bash
   docker-compose run --rm web python manage.py createsuperuser
   ```
6. **Ingresa al Administrador**:
   - Accede a `http://localhost:8000/admin/` e inicia sesión.
   - Crea un **Recinto** (ej: "Altiplano Norte").
   - Crea los **Planos**, súbeles una imagen (PNG/JPG del Piso 1 y Piso 2) y asócialos al Recinto.

7. **Importar el Catastro (CSV)**:
   - Asegúrate de colocar tu archivo CSV en la carpeta raíz del proyecto (junto a `manage.py`), por ejemplo `catastro.csv`.
   - Ejecuta el importador inteligente:
     ```bash
     docker-compose run --rm web python manage.py importar_catastro catastro.csv
     ```
   - Este comando leerá el CSV y dejará los equipos en la **Bandeja de Entrada** porque no tienen coordenadas X,Y aún.

8. **Usar la Aplicación**:
   - Navega a `http://localhost:8000/` (o la IP local de tu máquina en la red: `http://192.168.x.x:8000/`).
   - Selecciona el plano en el selector superior derecho (Piso 1, Piso 2, etc).
   - Arrastra los equipos desde la barra lateral izquierda hacia el punto deseado en el plano.
   - Las coordenadas se guardarán automáticamente (AJAX).
   - Haz clic en los equipos ya ubicados (iconos circulares azules) para ver sus datos técnicos y de conectividad (IP, AnyDesk).

## Exportar para Respaldos
Si necesitas exportar la base de datos (para respaldar o moverla a otro servidor):
```bash
docker-compose exec db pg_dump -U inventory_user -d inventory_db -F c -f /var/lib/postgresql/data/respaldo.dump
```
Y lo encontrarás en tu volumen de Docker bindeado o puedes hacerle un dump normal redireccionándolo.
