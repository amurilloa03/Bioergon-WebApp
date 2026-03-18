document.addEventListener('DOMContentLoaded', function () {
    // Toggle details buttons
    document.querySelectorAll('.btn-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const target = document.querySelector(btn.getAttribute('data-target'));
            if (!target) return;
            const expanded = btn.getAttribute('aria-expanded') === 'true';
            btn.setAttribute('aria-expanded', String(!expanded));
            target.classList.toggle('show');
        });
    });

    // Create-form modal (forms page)
    (function () {
        const fab = document.getElementById('fab-open');
        const backdrop = document.getElementById('modal-backdrop');
        const closeBtn = document.getElementById('modal-close');
        const cancel = document.getElementById('modal-cancel');
        if (!fab || !backdrop) return;

        function openModal() { backdrop.classList.add('show'); backdrop.setAttribute('aria-hidden', 'false'); const name = document.getElementById('form-nombre'); if (name) name.focus(); }
        function closeModal() { backdrop.classList.remove('show'); backdrop.setAttribute('aria-hidden', 'true'); }

        fab.addEventListener('click', openModal);
        closeBtn && closeBtn.addEventListener('click', closeModal);
        cancel && cancel.addEventListener('click', closeModal);

        backdrop.addEventListener('click', function (e) { if (e.target === backdrop) closeModal(); });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });
    })();

    // Path picker integration (forms page)
    (function () {
        const pathBtn = document.getElementById('path-button');
        const pathInput = document.getElementById('path-input-native');
        const pathDisplay = document.getElementById('path-display');
        const rutaInput = document.getElementById('form-ruta');
        if (!pathBtn || !pathInput || !pathDisplay || !rutaInput) return;

        pathBtn.addEventListener('click', function () { pathInput.click(); });

        pathInput.addEventListener('change', function () {
            if (!this.files || this.files.length === 0) return;
            let display = this.files[0].webkitRelativePath || this.files[0].name;
            if (this.files[0].webkitRelativePath) {
                const parts = display.split('/');
                parts.pop();
                display = parts.join('/') || display;
            }
            pathDisplay.textContent = display;
            pathDisplay.title = display;
            rutaInput.title = display;
            rutaInput.value = display;
        });
    })();

    // Perfil modal (profile page)
    (function () {
        const openBtn = document.getElementById('edit-profile-open');
        const backdrop = document.getElementById('modal-backdrop-perfil');
        const closeBtn = document.getElementById('modal-close-perfil');
        const cancelBtn = document.getElementById('modal-cancel-perfil');
        const form = document.getElementById('perfil-form');
        const errBox = document.getElementById('perfil-form-error');

        if (!openBtn || !backdrop) return;

        function openModal() { backdrop.classList.add('show'); backdrop.setAttribute('aria-hidden', 'false'); const nombre = document.getElementById('perfil-nombre'); if (nombre) nombre.focus(); }
        function closeModal() { backdrop.classList.remove('show'); backdrop.setAttribute('aria-hidden', 'true'); if (errBox) { errBox.style.display = 'none'; } }

        openBtn.addEventListener('click', openModal);
        closeBtn && closeBtn.addEventListener('click', closeModal);
        cancelBtn && cancelBtn.addEventListener('click', closeModal);
        backdrop.addEventListener('click', function (e) { if (e.target === backdrop) closeModal(); });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });

        if (form) {
            form.addEventListener('submit', function (e) {
                const correoEl = document.getElementById('perfil-correo');
                const cpostalEl = document.getElementById('perfil-c_postal');
                const correo = correoEl ? correoEl.value.trim() : '';
                const cpostal = cpostalEl ? cpostalEl.value.trim() : '';
                const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
                if (!emailPattern.test(correo)) {
                    e.preventDefault();
                    if (errBox) { errBox.textContent = 'El correo no tiene formato válido.'; errBox.style.display = 'block'; }
                    return false;
                }
                if (!/^[0-9]+$/.test(cpostal)) {
                    e.preventDefault();
                    if (errBox) { errBox.textContent = 'El código postal debe ser numérico.'; errBox.style.display = 'block'; }
                    return false;
                }
            });
        }
    })();

    // Generic AJAX handler for all inline-form actions (Delete, Visibility, Duplicate)
    document.querySelectorAll('.inline-form').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            const action = form.getAttribute('action');
            if (action.includes('/delete') && !confirm('¿Borrar este formulario?')) return;

            const isDuplicate = action.includes('/duplicate');
            const isVisibility = action.includes('/toggle_visibility');
            const isDelete = action.includes('/delete');

            const formData = new FormData(form);
            fetch(action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (isDelete) {
                            const card = form.closest('.form-card');
                            if (card) {
                                card.style.opacity = '0';
                                card.style.transform = 'scale(0.9)';
                                setTimeout(() => card.remove(), 300);
                            }
                        } else if (isVisibility) {
                            // Update visibility icon and styles
                            const img = form.querySelector('.icon-visibility');
                            if (img) {
                                const isNowVisible = data.visible;
                                img.src = isNowVisible ? '/static/images/ojo.png' : '/static/images/ojo_cerrado.png';
                                img.alt = isNowVisible ? 'Visible' : 'No visible';

                                const card = form.closest('.form-card');
                                if (card) {
                                    card.classList.toggle('is-hidden', !isNowVisible);
                                }
                            }
                        } else if (isDuplicate || data.redirect) {
                            // Reload if duplicating to show newest form
                            window.location.reload();
                        }
                    } else {
                        alert('Error: ' + (data.error || 'Ocurrió un problema inesperado.'));
                    }
                })
                .catch(err => {
                    console.error('AJAX form error:', err);
                    alert('Error de conexión.');
                });
        });
    });

});
