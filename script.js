document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links (reutilizado)
    document.querySelectorAll('nav a').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').split('#')[1]; // Get the ID after the hash
            if (targetId) {
                document.getElementById(targetId).scrollIntoView({
                    behavior: 'smooth'
                });
            } else {
                // If it's a full path (e.g., tickets.html), navigate normally
                window.location.href = this.getAttribute('href');
            }
        });
    });

    // Set 'active' class for current page in navigation (reutilizado)
    const currentPage = window.location.pathname.split('/').pop();
    document.querySelectorAll('nav a').forEach(link => {
        // If on index.html, only highlight "Inicio"
        if (currentPage === '' || currentPage === 'index.html') {
            if (link.getAttribute('href') === 'index.html') {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        } else if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Lógica del Modal de Compra
    const purchaseModal = document.getElementById('purchaseModal');
    const closeButton = document.querySelector('.close-button');
    const purchaseForm = document.getElementById('purchaseForm');
    const formProductName = document.getElementById('form-product-name');
    const formProductPrice = document.getElementById('form-product-price');
    const formPaypalUrl = document.getElementById('form-paypal-url'); // <-- Contiene la URL de PayPal

    // Abre el modal al hacer clic en "Comprar"
    document.querySelectorAll('.btn-buy').forEach(button => {
        button.addEventListener('click', function() {
            const productCard = this.closest('.product-card');
            const productName = productCard.dataset.name;
            const productPrice = productCard.dataset.price;
            const paypalUrl = this.dataset.paypal_url; // Obtener la URL de PayPal del botón (asegúrate de que el data-attribute sea 'data-paypal-url' en HTML)

            document.getElementById('modal-product-title').textContent = productName;
            formProductName.value = productName;
            formProductPrice.value = productPrice;
            formPaypalUrl.value = paypalUrl; // Asignar la URL de PayPal al input oculto

            purchaseModal.classList.add('active');
        });
    });

    // Cierra el modal
    closeButton.addEventListener('click', function() {
        purchaseModal.classList.remove('active');
        purchaseForm.reset(); // Opcional: Limpiar el formulario al cerrar el modal
    });

    // Cierra el modal al hacer clic fuera de su contenido
    window.addEventListener('click', function(event) {
        if (event.target === purchaseModal) {
            purchaseModal.classList.remove('active');
            purchaseForm.reset(); // Opcional: Limpiar el formulario al cerrar el modal
        }
    });

    /*
    // --- ESTE BLOQUE SE COMENTA/ELIMINA ---
    // La lógica de envío del formulario ahora será manejada directamente por la acción del formulario HTML.
    // El formulario se enviará al backend, y el backend se encargará de redirigir al usuario a la URL de PayPal.
    purchaseForm.addEventListener('submit', function(event) {
        event.preventDefault(); // Esto ya no es necesario si el formulario se envía directamente

        const formData = new FormData(purchaseForm);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        // Esta petición fetch ya no es necesaria y causaba el error CORS
        fetch('https://cast-sneakers-backend1.onrender.com/webhook/purchase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log('Respuesta del backend:', response);
            if (response.ok) {
                console.log('Formulario enviado a Formspree con éxito!');
                const paypalRedirectUrl = formPaypalUrl.value;
                window.location.href = paypalRedirectUrl;

                purchaseModal.classList.remove('active');
                purchaseForm.reset();
            } else {
                response.json().then(data => {
                    console.error('Error al enviar el formulario. Detalles:', data);
                    alert('Hubo un error al procesar tu solicitud: ' + (data.error || 'Por favor, inténtalo de nuevo. Revisa la consola para más información.'));
                }).catch(() => {
                    console.error('Error al enviar el formulario. No se pudieron obtener detalles de la respuesta JSON.');
                    alert('Hubo un error al procesar tu solicitud. Por favor, inténtalo de nuevo. Revisa la consola para más información.');
                });
            }
        })
        .catch(error => {
            console.error('ERROR DE RED (fetch failed):', error);
            alert('¡ERROR DE RED! Por favor, verifica tu conexión a internet. Si el problema persiste, contacta con soporte. Revisa la consola del navegador (F12 > Consola) para más detalles.');
        });
    });
    */
});