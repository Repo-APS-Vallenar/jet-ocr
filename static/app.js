// Inicialización de la Base de Datos Local
localforage.config({
    name: 'OCR_OfflineDB',
    storeName: 'fotos_pendientes'
});

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('ocr-form');
    const inputFotoCam = document.getElementById('foto-upload-camara');
    const btnProcesar = document.getElementById('btn-procesar');

    // Helper para obtener el archivo de cualquier input
    function getFotoFile() {
        if (inputFotoCam && inputFotoCam.files.length > 0) return inputFotoCam.files[0];
        return null;
    }

    // Elementos Offline
    const offlineToggle = document.getElementById('offline-mode-toggle');
    const offlineBar = document.getElementById('offline-status-bar');
    const queueCount = document.getElementById('queue-count');
    const btnSync = document.getElementById('btn-sync');
    const btnVerCartilla = document.getElementById('btn-ver-cartilla');
    const cartillaModal = document.getElementById('cartilla-modal');
    const cartillaContainer = document.getElementById('cartilla-items-container');
    const cartillaCount = document.getElementById('cartilla-count');
    let isOffline = false;

    // Labels y Secciones UI
    const fotoName = document.getElementById('foto-name');
    const loader = document.getElementById('loader');
    const resultsArea = document.getElementById('results-area');
    const uploadSection = document.querySelector('.upload-section');

    // Refrescar contador inicial de base de datos local al cargar la app
    actualizarContadorOffline();


    // Evento de Cambio de Modo (Online/Offline)
    offlineToggle.addEventListener('change', (e) => {
        isOffline = e.target.checked;
        if (isOffline) {
            offlineBar.classList.remove('hidden');
            btnProcesar.innerHTML = '<span><i class="fa-solid fa-hard-drive"></i> Guardar en Memoria</span>';
            btnProcesar.style.backgroundColor = '#f59e0b';
            btnProcesar.style.boxShadow = '0 4px 14px 0 rgba(245, 158, 11, 0.39)';
        } else {
            offlineBar.classList.add('hidden');
            btnProcesar.innerHTML = '<span><i class="fa-solid fa-wand-magic-sparkles"></i> Extraer y Actualizar</span>';
            btnProcesar.style.backgroundColor = 'var(--secondary)';
            btnProcesar.style.boxShadow = '0 4px 14px 0 rgba(59, 130, 246, 0.39)';
        }
    });

    const handleFileChange = (e) => {
        if (e.target.files.length > 0) {
            fotoName.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Archivo Listo: <strong>${e.target.files[0].name.substring(0,20)}...</strong>`;
            fotoName.style.color = '#047857';
            btnProcesar.disabled = false;
        }
    };

    if (inputFotoCam) inputFotoCam.addEventListener('change', handleFileChange);

    function checkValidForm() {
        if (getFotoFile()) {
            btnProcesar.disabled = false;
        }
    }

    // FORMULARIO PRINCIPAL (Guardar o Subir)
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const file = getFotoFile();
        if (!file) return;

        // Ocultar botón y mostrar loader
        btnProcesar.classList.add('hidden');
        loader.classList.remove('hidden');

        // --- OPTIMIZACIÓN: COMPRESIÓN EN EL CLIENTE ---
        const img = new Image();
        img.src = URL.createObjectURL(file);
        
        img.onload = async () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Redimensionar a un tamaño óptimo para OCR (1200px)
            const MAX_WIDTH = 1200;
            const MAX_HEIGHT = 1200;
            let width = img.width;
            let height = img.height;

            if (width > height) {
                if (width > MAX_WIDTH) { height *= MAX_WIDTH / width; width = MAX_WIDTH; }
            } else {
                if (height > MAX_HEIGHT) { width *= MAX_HEIGHT / height; height = MAX_HEIGHT; }
            }

            canvas.width = width;
            canvas.height = height;
            // Filtro de Contraste para potenciar la lectura de letras en OCR
            ctx.filter = 'contrast(1.2) saturate(1.05) brightness(1.02)';
            ctx.drawImage(img, 0, 0, width, height);
            ctx.filter = 'none'; // reset

            if (isOffline) {
                // --- MODO PASILLO: GUARDAR BASE64 COMPRIMIDO ---
                const base64Data = canvas.toDataURL('image/jpeg', 0.92); // 92% calidad para mejor lectura OCR
                const id = 'scan_' + Date.now();
                
                const scanData = {
                    id: id,
                    foto_b64: base64Data,
                    metadata: {
                        proyecto_id: document.getElementById('proyecto_id').value,
                        ubicacion: document.getElementById('ubicacion').value.trim(),
                        usuario: document.getElementById('usuario').value.trim(),
                        estado: document.getElementById('estado').value,
                        fecha: new Date().toISOString()
                    }
                };

                try {
                    await localforage.setItem(id, scanData);
                    actualizarContadorOffline();
                    loader.classList.add('hidden');
                    showResults({
                        status: 'success',
                        message: '¡Guardado Pro! Foto comprimida y persistida localmente.',
                        es_offline: true
                    });
                } catch (err) {
                    showResults({ status: 'error', message: 'Error al persistir en memoria local.' });
                }
            } else {
                // --- MODO DIRECTO: ENVIAR BLOB COMPRIMIDO ---
                canvas.toBlob(async (blob) => {
                    const formData = new FormData();
                    formData.append('foto', blob, 'foto.jpg');
                    formData.append('proyecto_id', document.getElementById('proyecto_id').value);
                    formData.append('ubicacion', document.getElementById('ubicacion').value.trim());
                    formData.append('usuario', document.getElementById('usuario').value.trim());
                    formData.append('estado', document.getElementById('estado').value);

                    try {
                        const response = await fetch('/api/procesar', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        showResults(data);
                    } catch (error) {
                        showResults({ status: 'error', message: 'Error de conexión con el Servidor.' });
                    }
                }, 'image/jpeg', 0.92);
            }
            URL.revokeObjectURL(img.src); // Liberar memoria
        };
    });

    // BOTÓN SINCRONIZAR
    btnSync.addEventListener('click', async () => {
        if (btnSync.disabled && btnSync.className.includes('processing')) return; 

        const keys = await localforage.keys();
        if (keys.length === 0) return alert("No hay fotos en memoria para sincronizar");

        // Reemplazo de confirm() nativo por modal personalizado
        const modal = document.getElementById('modal-sync');
        const desc = document.getElementById('modal-sync-desc');
        const btnCancel = document.getElementById('modal-sync-cancel');
        const btnConfirm = document.getElementById('modal-sync-confirm');

        desc.innerHTML = `Detectamos <strong>${keys.length} fotos</strong> en la cola de subida offline. Se procesarán de golpe a texto.`;
        modal.style.display = 'flex';

        const confirmarSincronizacion = () => {
            return new Promise((resolve) => {
                const onCancel = () => {
                    modal.style.display = 'none';
                    limpiarEventos();
                    resolve(false);
                };
                const onConfirm = () => {
                    modal.style.display = 'none';
                    limpiarEventos();
                    resolve(true);
                };
                const limpiarEventos = () => {
                    btnCancel.removeEventListener('click', onCancel);
                    btnConfirm.removeEventListener('click', onConfirm);
                };
                btnCancel.addEventListener('click', onCancel);
                btnConfirm.addEventListener('click', onConfirm);
            });
        };

        const continuar = await confirmarSincronizacion();
        if (!continuar) return;

        btnSync.disabled = true;
        btnSync.classList.add('processing');

        form.classList.add('hidden');
        loader.classList.remove('hidden');

        const progressContainer = document.getElementById('sync-progress-container');
        const progressBar = document.getElementById('sync-progress-bar');
        if (progressContainer) progressContainer.style.display = 'block';

        let syncedCount = 0;
        let errores = [];

        try {
            for (let i = 0; i < keys.length; i++) {
                const key = keys[i];
                const scanData = await localforage.getItem(key);
                
                // Actualizar texto y barra
                document.querySelector('.loader-text').innerHTML = `Sincronizando equipo <strong style="color:#2563eb">${i + 1} de ${keys.length}</strong>...<br><span style="font-size:0.8rem; color:#64748b;">No cierres esta pestaña.</span>`;
                if (progressBar) {
                    let pct = ((i + 1) / keys.length) * 100;
                    progressBar.style.width = pct + '%';
                }

                try {
                    // Enviar de una en una usando la API batch existente (con un array de 1 item)
                    const response = await fetch('/api/procesar_batch', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ scaneos: [scanData] })
                    });
                    const resData = await response.json();

                    if (resData.status === 'success') {
                        await localforage.removeItem(key); // Borrar solo si se procesó bien
                        syncedCount++;
                    } else {
                        // NO BORRAR: Guardar el mensaje de error para que se vea en la cartilla
                        scanData.error_sync = resData.message || 'Fallo desconocido';
                        await localforage.setItem(key, scanData);
                        errores.push(`ID ${key}: ${resData.message}`);
                    }
                } catch (e) {
                    errores.push(`ID ${key}: Error de conexión`);
                }
            }

            actualizarContadorOffline();

            if (progressContainer) progressContainer.style.display = 'none';

            let msg = `Sincronización finalizada. Éxito: ${syncedCount}/${keys.length}.`;
            if (errores.length > 0) {
                msg += ` Fallidos: ${errores.length}. Revisa consola para detalles.`;
                console.error("Errores Sync:", errores);
            }

            showResults({
                status: errores.length === 0 ? 'success' : 'warning',
                message: msg,
                es_batch: true
            });

            btnSync.disabled = false;
            btnSync.classList.remove('processing');

        } catch (error) {
            form.classList.remove('hidden');
            loader.classList.add('hidden');
            if (progressContainer) progressContainer.style.display = 'none';
            btnSync.disabled = false;
            btnSync.classList.remove('processing');
            alert("Error crítico durante la sincronización.");
        }
    });

    async function actualizarContadorOffline() {
        const keys = await localforage.keys();
        queueCount.textContent = keys.length;
        if (keys.length > 0) {
            btnSync.disabled = false;
            btnVerCartilla.style.display = 'inline-block';
        } else {
            btnSync.disabled = true;
            btnVerCartilla.style.display = 'none';
        }
    }

    // === LÓGICA DE CARTILLA OFFLINE ===
    btnVerCartilla.addEventListener('click', async () => {
        cartillaContainer.innerHTML = '<div style="text-align:center; padding: 20px;"><div class="spinner"></div></div>';
        cartillaModal.classList.remove('hidden');
        
        const keys = await localforage.keys();
        cartillaCount.textContent = keys.length;
        
        if (keys.length === 0) {
            cartillaContainer.innerHTML = '<p style="text-align:center; color:#64748b; margin-top: 30px;">No hay equipos en la cola offline.</p>';
            return;
        }

        let htmlChunks = [];
        for (let key of keys) {
            const data = await localforage.getItem(key);
            const m = data.metadata || {};
            
            htmlChunks.push(`
                <div class="cartilla-item" style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; display: flex; gap: 12px; background: #f8fafc; align-items: flex-start;">
                    <img src="${data.foto_b64}" onclick="abrirVisorImagen(this.src)" style="cursor: pointer; width: 80px; height: 80px; object-fit: cover; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" title="Toca para ampliar" />
                    <div style="flex: 1; display: flex; flex-direction: column; gap: 8px;">
                        <div style="display: flex; gap: 8px;">
                            <input type="text" id="sn_${key}" class="meta-input" value="${m.sn || ''}" placeholder="S/N (Manual u OCR)" title="Número de Serie" style="padding: 4px 8px; font-size: 0.85rem; flex: 1; border-color: #f59e0b;" />
                            <input type="text" id="mac_${key}" class="meta-input" value="${m.mac || ''}" placeholder="MAC (Manual)" title="Dirección MAC" style="padding: 4px 8px; font-size: 0.85rem; flex: 1; border-color: #22c55e;" />
                        </div>
                        <input type="text" id="loc_${key}" class="meta-input" value="${m.ubicacion || ''}" placeholder="Ubicación/Box" style="padding: 4px 8px; font-size: 0.85rem;" />
                        <input type="text" id="usr_${key}" class="meta-input" value="${m.usuario || ''}" placeholder="Usuario (opcional)" style="padding: 4px 8px; font-size: 0.85rem;" />
                        <div style="display: flex; gap: 8px;">
                            <select id="est_${key}" class="meta-select" style="padding: 4px 8px; font-size: 0.85rem; flex: 1;">
                                <option value="En Bodega" ${m.estado==='En Bodega'?'selected':''}>En Bodega / Sin asignar</option>
                                <option value="Asignado" ${m.estado==='Asignado'?'selected':''}>Asignado / En uso</option>
                                <option value="En reparación" ${m.estado==='En reparación'?'selected':''}>En reparación</option>
                                <option value="Baja" ${m.estado==='Baja'?'selected':''}>De baja</option>
                            </select>
                            <button type="button" onclick="guardarItemCartilla('${key}')" title="Guardar cambios" style="background:#3b82f6; color:white; border:none; border-radius:6px; padding:4px 10px; font-size:0.8rem; cursor:pointer;"><i class="fa-solid fa-floppy-disk"></i></button>
                            <button type="button" onclick="eliminarItemCartilla('${key}')" title="Eliminar registro" style="background:#ef4444; color:white; border:none; border-radius:6px; padding:4px 10px; font-size:0.8rem; cursor:pointer;"><i class="fa-solid fa-trash"></i></button>
                        </div>
                        <!-- ALERTA DE ERROR SI FALLÓ SYNC -->
                        ${data.error_sync ? `
                            <div style="font-size: 0.72rem; color: #b91c1c; background: #fef2f2; padding: 6px 10px; border-radius: 6px; border: 1px solid #fecaca; margin-top: 4px; display: flex; align-items: center; gap: 4px;">
                                <i class="fa-solid fa-circle-exclamation"></i> <strong>Error:</strong> ${data.error_sync}
                            </div>
                        ` : ''}
                        <span id="msg_${key}" style="font-size: 0.75rem; color: #22c55e; display: none; font-weight: bold;"><i class="fa-solid fa-check"></i> Modificado</span>
                    </div>
                </div>
            `);
        }
        cartillaContainer.innerHTML = htmlChunks.join('');
    });

    document.getElementById('btn-cerrar-cartilla').addEventListener('click', () => {
        cartillaModal.classList.add('hidden');
    });

    document.getElementById('btn-sync-from-cartilla').addEventListener('click', () => {
        cartillaModal.classList.add('hidden');
        btnSync.click();
    });

    // === LÓGICA DEL VISOR DE IMÁGENES ===
    const imageViewerModal = document.getElementById('image-viewer-modal');
    const visorImg = document.getElementById('visor-img');

    window.abrirVisorImagen = function(src) {
        visorImg.src = src;
        imageViewerModal.classList.remove('hidden');
    };

    document.getElementById('btn-cerrar-visor').addEventListener('click', () => {
        imageViewerModal.classList.add('hidden');
    });
    
    // Cerrar el visor si tocan el fondo negro
    imageViewerModal.addEventListener('click', (e) => {
        if (e.target === imageViewerModal) {
            imageViewerModal.classList.add('hidden');
        }
    });

    // Helper global para que actualizarContadorOffline pueda ser llamado desde windows (on delete)
    window.refrescarEstadoGlobalOffline = actualizarContadorOffline;
});

function showResults(data) {
    document.querySelector('.upload-section').classList.add('hidden');
    document.getElementById('results-area').classList.remove('hidden');

    const title = document.getElementById('result-title');
    const icon = document.getElementById('status-icon');
    const message = document.getElementById('result-message');
    const dataGrid = document.getElementById('data-grid');
    const btnDownload = document.getElementById('btn-download');

    message.textContent = data.message;
    icon.className = 'status-icon ' + data.status;

    // === CASO DUPLICADO / NO ENCONTRADO: Mostrar pantalla inteligente ===
    if (data.status === 'duplicate' || data.status === 'not_found' || data.status === 'warning') {
        // Ocultar upload y resultados, mostrar panel de duplicados
        document.querySelector('.upload-section').classList.add('hidden');
        document.getElementById('results-area').classList.add('hidden');
        document.getElementById('duplicate-area').classList.remove('hidden');

        // Configurar previsualización de imagen si existe
        const imgContainer = document.getElementById('dup-preview-container');
        const imgPreview = document.getElementById('dup-preview-img');
        if (data.imagen_b64) {
            imgPreview.src = 'data:image/jpeg;base64,' + data.imagen_b64;
            imgContainer.style.display = 'block';
        } else {
            imgContainer.style.display = 'none';
        }

        // Configurar Títulos y comportamiento según el error
        let esNoEncontrado = data.status === 'not_found' || data.status === 'warning';

        if (data.status === 'warning' && !data.sn && !data.mac) {
            document.getElementById('dup-title').textContent = "Ingreso Manual Requerido";
        } else if (esNoEncontrado) {
            document.getElementById('dup-title').textContent = "S/N No Encontrado o Inválido";
        } else {
            document.getElementById('dup-title').textContent = "Equipo ya registrado / Revisar Datos";
        }

        // Mostrar los datos en los inputs editables
        document.getElementById('dup-input-sn').value = data.sn || '';
        document.getElementById('dup-input-mac').value = data.existente?.mac || data.mac || '';

        document.getElementById('dup-equipo').textContent = data.equipo_nombre || '-';

        const dup = data.existente || {};
        // Pre-rellenar con lo que ya existe en la BD
        document.getElementById('dup-ubicacion').value = dup?.ubicacion || '';
        document.getElementById('dup-usuario').value = dup?.usuario || '';
        // Pre-seleccionar estado si existe
        if (dup?.estado) {
            const estadoSel = document.getElementById('dup-estado');
            for (let opt of estadoSel.options) {
                if (opt.value === dup.estado || opt.text === dup.estado) {
                    opt.selected = true; break;
                }
            }
        }

        // Mensaje contextual inteligente según lo que falta
        const dupMsg = document.getElementById('dup-message');
        if (esNoEncontrado) {
            dupMsg.textContent = data.message;
            dupMsg.style.borderColor = '#ef4444';
        } else {
            let camposFaltantes = [];
            if (!dup?.ubicacion) camposFaltantes.push('Ubicación');
            if (!dup?.usuario) camposFaltantes.push('Usuario');

            if (camposFaltantes.length > 0) {
                dupMsg.textContent = `Este equipo ya fue registrado, pero le faltan datos: ${camposFaltantes.join(', ')}. Complétalos abajo.`;
                dupMsg.style.borderColor = '#f59e0b';
            } else {
                dupMsg.textContent = 'Este equipo ya está registrado completamente. Solo edita si necesitas actualizar algo.';
                dupMsg.style.borderColor = '#22c55e';
            }
        }
        return; // Salimos para no dibujar la pantalla normal
    }

    // === CASO MÚLTIPLES EQUIPOS EN UNA FOTO ===
    if (data.multiples) {
        document.querySelector('.upload-section').classList.add('hidden');
        document.getElementById('results-area').classList.add('hidden');
        document.getElementById('duplicate-area').classList.add('hidden');
        document.getElementById('multi-area').classList.remove('hidden');

        document.getElementById('multi-message').textContent = data.message;
        const container = document.getElementById('multi-cards-container');
        container.innerHTML = ''; // Limpiar tarjetas anteriores

        data.equipos.forEach((eq, idx) => {
            container.appendChild(crearEquipoCard(eq, idx));
        });
        return;
    }

    if (data.status === 'success') {
        icon.innerHTML = '<i class="fa-solid fa-circle-check"></i>';

        // 🎉 Efecto Premium: Confetti para éxitos en línea
        if (!data.es_offline && typeof confetti === 'function') {
            confetti({
                particleCount: 120,
                spread: 80,
                origin: { y: 0.6 },
                zIndex: 9999
            });
        }

        if (data.es_offline) {
            title.textContent = '¡En Memoria!';
            title.style.color = '#f59e0b';
        } else if (data.es_batch) {
            title.textContent = '¡Sincronización Exitosa!';
            title.style.color = '#22c55e';
            btnDownload.classList.remove('hidden');
        } else {
            title.textContent = '¡Etiqueta Registrada!';
            title.style.color = '#22c55e';
            dataGrid.classList.remove('hidden');
            document.getElementById('res-equipo').textContent = data.equipo_nombre;
            document.getElementById('res-sn').textContent = data.sn;
            document.getElementById('res-mac').textContent = data.mac;
            btnDownload.classList.remove('hidden');
        }

    } else if (data.status === 'warning') {
        icon.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
        title.textContent = 'Atención (Parcial)';
        title.style.color = '#f59e0b';

        // Lote warning
        if (data.es_batch) btnDownload.classList.remove('hidden');

        if (data.sn && !data.es_batch) {
            dataGrid.classList.remove('hidden');
            document.getElementById('res-equipo').textContent = data.equipo_nombre || '-';
            document.getElementById('res-sn').textContent = data.sn || '-';
            document.getElementById('res-mac').textContent = data.mac || '-';
        }

    } else {
        icon.innerHTML = '<i class="fa-solid fa-circle-xmark"></i>';
        title.textContent = 'Error Lógico';
        title.style.color = '#ef4444';
    }
}

function resetForm() {
    document.getElementById('results-area').classList.add('hidden');
    document.getElementById('duplicate-area').classList.add('hidden');
    document.getElementById('multi-area').classList.add('hidden');
    document.querySelector('.upload-section').classList.remove('hidden');

    // Restaurar el formulario dentro de upload-section si fue tapado por sync
    document.getElementById('ocr-form').classList.remove('hidden');

    const btnProcesar = document.getElementById('btn-procesar');
    btnProcesar.classList.remove('hidden');
    document.getElementById('loader').classList.add('hidden');

    if (inputFotoCam) inputFotoCam.value = '';
    document.getElementById('foto-name').innerHTML = "";

    btnProcesar.disabled = true;
    document.getElementById('data-grid').classList.add('hidden');
    document.getElementById('btn-download').classList.add('hidden');
}

// === FORMULARIO DE ACTUALIZACIÓN PARCIAL DE DUPLICADOS ===
document.addEventListener('DOMContentLoaded', () => {
    const dupForm = document.getElementById('dup-form');
    if (!dupForm) return;

    dupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(dupForm);

        // Agregar forzosamente los valores de los inputs editables que están fuera del form
        formData.set('sn', document.getElementById('dup-input-sn').value.trim());
        formData.set('mac', document.getElementById('dup-input-mac').value.trim());
        formData.set('proyecto_id', document.getElementById('proyecto_id').value);

        try {
            // Usamos el mismo endpoint pero enviando solo metadatos y sn (sin foto)
            const response = await fetch('/api/actualizar_meta', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            // Ocultar panel de duplicados y mostrar resultado
            document.getElementById('duplicate-area').classList.add('hidden');
            data.es_parcial = true;
            showResults(data);

        } catch (err) {
            alert('No se pudo conectar al servidor. Verifica el WiFi.');
        }
    });
});

// === GENERADOR DE TARJETAS MULTI-EQUIPO ===
function crearEquipoCard(eq, idx) {
    const card = document.createElement('div');
    card.className = `equipo-card status-${eq.status}`;

    const labelBadge = {
        success: '✅ Registrado',
        duplicate: '⚠️ Ya existía',
        error: '❌ No encontrado',
        warning: '⚠️ Atención'
    };

    let snFieldHTML = `<div class="equipo-data-item"><strong>S/N</strong><span>${eq.sn || '-'}</span></div>`;
    let btnText = '<i class="fa-solid fa-pencil"></i> Completar / editar datos';
    let extraHidden = '';

    const esNoEncontrado = (eq.status === 'not_found' || eq.status === 'warning');

    if (esNoEncontrado) {
        snFieldHTML = `
            <div class="equipo-data-item" style="background:#fef3c7; border: 1px solid #f59e0b; padding:4px 8px; border-radius:4px;">
                <strong><i class="fa-solid fa-pen" style="color:#f59e0b"></i> Confirmar S/N</strong>
                <input type="text" class="meta-input equipo-sn-edit" style="width:140px; padding:2px 8px; font-size:0.85rem; border-color:#f59e0b; color:#92400e;" value="${eq.sn || ''}" required>
            </div>
        `;
        btnText = '<i class="fa-solid fa-floppy-disk"></i> Confirmar S/N o Forzar Creación';
    }

    card.innerHTML = `
        <div class="equipo-card-header">
            <span>Equipo ${idx + 1}${eq.equipo_nombre ? ' — ' + eq.equipo_nombre : ''}</span>
            <span class="equipo-badge ${eq.status}">${labelBadge[eq.status] || eq.status}</span>
        </div>
        <div class="equipo-data">
            ${snFieldHTML}
            <div class="equipo-data-item"><strong>MAC</strong><span>${eq.existente?.mac || eq.mac || '-'}</span></div>
        </div>
        <button class="equipo-meta-toggle" type="button">
            ${btnText}
        </button>
        <div class="equipo-meta-form-inner">
            <div class="meta-row">
                <label class="meta-label"><i class="fa-solid fa-location-dot" style="color:#3b82f6"></i> Ubicación / Box</label>
                <input type="text" class="meta-input equipo-ubicacion" value="${(eq.existente?.ubicacion || '')}" placeholder="Ej: Oficina 201">
            </div>
            <div class="meta-row">
                <label class="meta-label"><i class="fa-solid fa-user" style="color:#8b5cf6"></i> Usuario <span class="optional-tag">(opcional)</span></label>
                <input type="text" class="meta-input equipo-usuario" value="${(eq.existente?.usuario || '')}" placeholder="Nombre del usuario">
            </div>
            <div class="meta-row">
                <label class="meta-label"><i class="fa-solid fa-circle-dot" style="color:#22c55e"></i> Estado</label>
                <select class="meta-select equipo-estado">
                    <option value="En Bodega">En Bodega / Sin asignar</option>
                    <option value="Asignado">Asignado / En uso</option>
                    <option value="En reparación">En reparación</option>
                    <option value="Baja">De baja</option>
                </select>
            </div>
            <button class="equipo-btn-save" type="button">
                <i class="fa-solid fa-floppy-disk"></i> Guardar datos
            </button>
            <p class="equipo-save-msg" style="font-size:0.8rem;color:#22c55e;display:none">✅ Guardado correctamente</p>
        </div>
    `;

    // Pre-seleccionar estado si existe
    const estadoExistente = eq.existente?.estado;
    if (estadoExistente) {
        const sel = card.querySelector('.equipo-estado');
        for (let opt of sel.options) {
            if (opt.value === estadoExistente) { opt.selected = true; break; }
        }
    }

    // Toggle acordeón
    card.querySelector('.equipo-meta-toggle').addEventListener('click', () => {
        card.querySelector('.equipo-meta-form-inner').classList.toggle('open');
    });

    // Si al equipo le faltan datos o no se encontró, abrir el acordeón automáticamente
    if (esNoEncontrado || (eq.status === 'success' && (!eq.existente?.ubicacion || !eq.existente?.usuario))) {
        card.querySelector('.equipo-meta-form-inner').classList.add('open');
    }

    // Botón guardar metadatos inline
    card.querySelector('.equipo-btn-save').addEventListener('click', async () => {
        const inputSnEditable = card.querySelector('.equipo-sn-edit');
        const finalSn = inputSnEditable ? inputSnEditable.value.trim() : eq.sn;

        if (!finalSn) {
            alert('El S/N no puede estar vacío.');
            return;
        }

        const fd = new FormData();
        fd.append('sn', finalSn);

        // Si fue una corrección manual o forzada, enviamos la MAC leída por OCR
        if (esNoEncontrado || eq.status === 'duplicate') {
            fd.append('mac', eq.existente?.mac || eq.mac);
            fd.append('forzar_actualizacion', 'true');
        }
        fd.append('ubicacion', card.querySelector('.equipo-ubicacion').value.trim());
        fd.append('usuario', card.querySelector('.equipo-usuario').value.trim());
        fd.append('estado', card.querySelector('.equipo-estado').value);

        try {
            const resp = await fetch('/api/actualizar_meta', { method: 'POST', body: fd });
            const result = await resp.json();
            const msg = card.querySelector('.equipo-save-msg');
            if (result.status === 'success') {
                msg.innerHTML = `
                    <div class="font-bold text-emerald-600 mb-1">¡Éxito! Equipo registrado en el Inventario.</div>
                    <div class="text-xs text-slate-500">S/N: ${result.sn || finalSn} | MAC: ${result.mac || (eq.existente?.mac || eq.mac || '-')}</div>
                `;
                msg.style.display = 'block';
                setTimeout(() => {
                    msg.style.display = 'none';
                    card.querySelector('.equipo-meta-form-inner').classList.remove('open');
                }, 3000); // Increased timeout to allow user to see the message and button
            } else {
                alert(result.message);
            }
        } catch (err) {
            alert('Error de conexión con el servidor.');
        }
    });

    return card;
}

// === FUNCIONALIDADES GLOBALES DE LA CARTILLA OFFLINE ===
window.guardarItemCartilla = async function(key) {
    const data = await localforage.getItem(key);
    if (!data) return;
    
    data.metadata.sn = document.getElementById('sn_' + key).value.trim();
    data.metadata.mac = document.getElementById('mac_' + key).value.trim();
    data.metadata.ubicacion = document.getElementById('loc_' + key).value;
    data.metadata.usuario = document.getElementById('usr_' + key).value;
    data.metadata.estado = document.getElementById('est_' + key).value;
    
    await localforage.setItem(key, data);
    
    const msg = document.getElementById('msg_' + key);
    msg.style.display = 'block';
    setTimeout(() => msg.style.display = 'none', 2000);
}

window.eliminarItemCartilla = async function(key) {
    if(!confirm("¿Deseas eliminar esta foto de la cola? Se perderá permanentemente y no se sincronizará.")) return;
    
    await localforage.removeItem(key);
    
    // Refrescar modal de cartilla
    document.getElementById('btn-ver-cartilla').click();
    
    // Refrescar contador global
    if (window.refrescarEstadoGlobalOffline) {
        window.refrescarEstadoGlobalOffline();
    }
}
