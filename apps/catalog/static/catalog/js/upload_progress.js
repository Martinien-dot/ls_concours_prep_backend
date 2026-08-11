document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('#epreuve_form') || document.querySelector('form');
    if (!form) return;

    // 1. Ajouter les animations CSS pour le statut d'attente R2
    const style = document.createElement('style');
    style.innerHTML = `
        @keyframes pulse-text {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }
        .sync-r2 {
            color: #fbbf24; /* Orange/Yellow */
            animation: pulse-text 1.5s infinite;
            font-size: 11px;
            font-weight: bold;
        }
    `;
    document.head.appendChild(style);

    form.addEventListener('submit', function (e) {
        const fileInputs = form.querySelectorAll('input[type="file"]');
        const activeUploads = [];
        let totalPayloadSize = 0;

        fileInputs.forEach(input => {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                const startByte = totalPayloadSize;
                totalPayloadSize += file.size;
                const endByte = totalPayloadSize;

                activeUploads.push({
                    input: input,
                    file: file,
                    startByte: startByte,
                    endByte: endByte,
                    size: file.size,
                    isSyncing: false // Nouveau drapeau pour l'étape 2
                });
            }
        });

        if (activeUploads.length === 0) return;

        e.preventDefault();

        // 2. Créer l'interface des barres de progression
        activeUploads.forEach(item => {
            let container = item.input.parentNode.querySelector('.file-upload-progress');
            if (!container) {
                container = document.createElement('div');
                container.className = 'file-upload-progress';
                container.style.cssText = `
                    margin-top: 8px;
                    padding: 8px 12px;
                    background: #1e293b;
                    border-radius: 6px;
                    color: #ffffff;
                    font-family: Roboto, sans-serif;
                    font-size: 12px;
                    max-width: 500px;
                `;

                const fileSizeMB = (item.file.size / (1024 * 1024)).toFixed(2);
                container.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span><strong>${item.file.name}</strong> (${fileSizeMB} MB)</span>
                        <span class="file-percent" style="font-weight: bold; color: #38bdf8;">0%</span>
                    </div>
                    <div style="width: 100%; background: #334155; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div class="file-bar" style="width: 0%; height: 100%; background: #0ea5e9; transition: width 0.15s linear;"></div>
                    </div>
                `;
                item.input.parentNode.appendChild(container);
            }

            item.barEl = container.querySelector('.file-bar');
            item.percentEl = container.querySelector('.file-percent');
        });

        const submitButtons = form.querySelectorAll('input[type="submit"], button[type="submit"]');
        submitButtons.forEach(btn => btn.disabled = true);

        const formData = new FormData(form);
        const xhr = new XMLHttpRequest();

        // 3. Traquer la progression
        xhr.upload.addEventListener('progress', function (event) {
            if (event.lengthComputable) {
                const loadedBytes = event.loaded;

                activeUploads.forEach(item => {
                    let percent = 0;
                    if (loadedBytes >= item.endByte) {
                        percent = 100;
                    } else if (loadedBytes > item.startByte) {
                        const fileLoaded = loadedBytes - item.startByte;
                        percent = Math.min(100, Math.round((fileLoaded / item.size) * 100));
                    }

                    if (percent < 100) {
                        item.barEl.style.width = percent + '%';
                        item.percentEl.innerText = percent + '%';
                    }
                    // Quand l'upload navigateur -> serveur est fini, afficher l'attente Cloudflare R2
                    else if (percent === 100 && !item.isSyncing) {
                        item.isSyncing = true;
                        item.barEl.style.width = '100%';
                        item.barEl.style.background = '#10b981'; // Passe au vert
                        item.percentEl.innerHTML = '<span class="sync-r2">Envoi vers R2...</span>';
                    }
                });
            }
        });

        xhr.addEventListener('load', function () {
            if (xhr.status >= 200 && xhr.status < 400) {
                window.location.href = xhr.responseURL || window.location.href;
            } else {
                alert(`Erreur du serveur (${xhr.status}). Le transfert a échoué.`);
                submitButtons.forEach(btn => btn.disabled = false);
            }
        });

        xhr.addEventListener('error', function () {
            alert("Erreur réseau : la connexion a été interrompue par le serveur.");
            submitButtons.forEach(btn => btn.disabled = false);
        });

        // 4. PREPARATION ET ENVOI DE LA REQUETE (Correction de l'ordre d'exécution)

        // A. Ouvrir d'abord la connexion
        xhr.open('POST', form.action || window.location.href);

        // B. Ajouter le Header CSRF
        const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            xhr.setRequestHeader('X-CSRFToken', csrfInput.value);
        }

        // C. Récupérer le bouton cliqué (Enregistrer, Continuer, etc.)
        const activeElement = document.activeElement;
        if (activeElement && activeElement.name) {
            formData.append(activeElement.name, activeElement.value);
        }

        // D. Envoyer les données
        xhr.send(formData);
    });
});