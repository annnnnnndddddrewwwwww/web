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
    const closeButton = document.querySelector('.modal .close-button');
    const openModalButtons = document.querySelectorAll('.open-modal-btn');
    const modalProductTitle = document.getElementById('modal-product-title');
    const formProductName = document.getElementById('form-product-name');
    const formProductPrice = document.getElementById('form-product-price');
    const formPaypalUrl = document.getElementById('form-paypal-url');
    const purchaseForm = document.getElementById('purchaseForm');

    openModalButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productName = this.dataset.productName;
            const productPrice = this.dataset.productPrice;
            const paypalUrl = this.dataset.paypalUrl;

            modalProductTitle.textContent = productName;
            formProductName.value = productName;
            formProductPrice.value = productPrice;
            formPaypalUrl.value = paypalUrl;

            purchaseModal.classList.add('active');
        });
    });

    closeButton.addEventListener('click', function() {
        purchaseModal.classList.remove('active');
        // Limpiar el formulario al cerrar si es necesario
        purchaseForm.reset();
    });

    // Cerrar modal al hacer clic fuera del contenido
    window.addEventListener('click', function(event) {
        if (event.target === purchaseModal) {
            purchaseModal.classList.remove('active');
            purchaseForm.reset();
        }
    });

    // Manejar el envío del formulario del modal
    purchaseForm.addEventListener('submit', function(e) {
        e.preventDefault(); // Previene el envío estándar del formulario

        const formAction = this.action;
        const formData = new FormData(this);

        fetch(formAction, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => {
            console.log('Respuesta cruda de Formspree:', response); // <-- Añadido para depuración
            if (response.ok) {
                console.log('Formulario enviado a Formspree con éxito!');
                // Ahora, redirigir al usuario a PayPal
                const paypalRedirectUrl = formPaypalUrl.value;
                window.location.href = paypalRedirectUrl;

                purchaseModal.classList.remove('active');
                purchaseForm.reset();
            } else {
                // Intenta obtener más detalles del error si la respuesta no es 200 OK
                response.json().then(data => {
                    console.error('Error al enviar el formulario a Formspree. Detalles:', data);
                    alert('Hubo un error al procesar tu solicitud: ' + (data.error || 'Por favor, inténtalo de nuevo. Revisa la consola para más información.'));
                }).catch(() => {
                    console.error('Error al enviar el formulario a Formspree. No se pudieron obtener detalles de la respuesta JSON.');
                    alert('Hubo un error al procesar tu solicitud. Por favor, inténtalo de nuevo. Revisa la consola para más información.');
                });
            }
        })
        .catch(error => {
            console.error('ERROR DE RED (fetch failed):', error);
            alert('¡ERROR DE RED! Por favor, verifica tu conexión a internet. Si el problema persiste, contacta con soporte. Revisa la consola del navegador (F12 > Consola) para más detalles.');
        });
    });
});