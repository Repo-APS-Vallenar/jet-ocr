# 🚀 Guía de Despliegue en Producción — JET OCR

Para lanzar esta plataforma a producción de forma profesional y segura, necesitas un **Servidor Privado Virtual (VPS)** y configuración **HTTPS** (El navegador bloquea la cámara por seguridad si no hay certificado SSL).

---

## 📋 Requisitos del Servidor (VPS)
*   **SO Recomendado**: Ubuntu 22.04 LTS.
*   **RAM**: **4 GB mínimo** (Recomendado 8 GB). EasyOCR y PyTorch cargan modelos en memoria y consumen recursos al procesar imágenes simultáneas.
*   **Servidores**: DigitalOcean, AWS, Hostinger (Planes KVM), Vultr, etc.

---

## 🛠️ Paso 1: Configuración Inicial del VPS
Conéctate por SSH y corre:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git curl -y
```

---

## 📂 Paso 2: Descargar el Código
```bash
cd /var/www
# Clona tu repositorio de GitHub (O súbelo por FileZilla/SFTP)
git clone https://github.com/tu-usuario/tu-repositorio.git jet_ocr
cd jet_ocr
```

---

## 🐍 Paso 3: Entorno Virtual y Dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Servidor de producción para Flask
```

---

## 🔑 Paso 4: Variables de Entorno (.env)
Crea y edita el archivo:
```bash
nano .env
```
Pega estas variables ajustadas a tu producción:
```text
SECRET_KEY=UnaCadenaSuperSecretaYAlAzar123
DATABASE_URL=postgresql://usuariosupabase:password@aws-pooler.supabase.com:5432/postgres
MP_ACCESS_TOKEN=APP_USR-tu-token-de-mercadopago-de-produccion
```

---

## ⚙️ Paso 5: Crear Servicio en Segundo Plano (Systemd)
Para que la app no se apague nunca. Crea el archivo de servicio:
```bash
sudo nano /etc/systemd/system/jetocr.service
```

Pega el siguiente bloque de texto:
```ini
[Unit]
Description=Gunicorn instance to serve JET OCR
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/jet_ocr
Environment="PATH=/var/www/jet_ocr/venv/bin"
EnvironmentFile=/var/www/jet_ocr/.env
ExecStart=/var/www/jet_ocr/venv/bin/gunicorn --workers 3 --bind unix:jetocr.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

Guarda (`CTRL+O`, `Enter`) y sal (`CTRL+X`). Enciende el servicio:
```bash
sudo systemctl start jetocr
sudo systemctl enable jetocr
```

---

## 🌐 Paso 6: Configurar Reverse Proxy (Nginx)
Crea la configuración de tu dominio:
```bash
sudo nano /etc/nginx/sites-available/jetocr
```

Pega esto (Reemplaza `tudominio.com` por el tuyo):
```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/jet_ocr/jetocr.sock;
    }
}
```

Actívalo y reinicia Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/jetocr /etc/nginx/sites-enabled/
sudo nginx -t  # Probar que esté bien escrito
sudo systemctl restart nginx
```

---

## 🔒 Paso 7: Activar HTTPS (Gratis con Certbot)
**¡Obligatorio para que la cámara del celular funcione!**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d tudominio.com -d www.tudominio.com
```
Sigue las instrucciones en pantalla, dile que sí a la redirección de tráfico, y **¡LISTO!** 🚀 Tu SaaS está corriendo seguro y escalable.
