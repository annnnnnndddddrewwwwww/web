document.addEventListener('DOMContentLoaded', function() {
    console.log("¡script.js cargado y DOM listo!"); // Debugging log: Esto debería aparecer al cargar la página.

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
    const formPaypalUrl = document.getElementById('form-paypal-url');

    // DEBUG: Log the elements found by querySelectorAll
    const buyButtons = document.querySelectorAll('.btn-buy');
    console.log("Botones '.btn-buy' encontrados:", buyButtons); // Debugging log: Debería mostrar una NodeList con tus botones.

    // Abre el modal al hacer clic en "Comprar"
    buyButtons.forEach(button => {
        console.log("Añadiendo event listener al botón:", button); // Debugging log: Debería aparecer por cada botón "Comprar".
        button.addEventListener('click', function() {
            console.log("¡Botón 'Comprar' clickeado!"); // Debugging log: Debería aparecer al hacer clic en "Comprar".

            const productCard = this.closest('.product-card');
            console.log("Tarjeta de producto encontrada:", productCard); // Debugging log: Debería mostrar el elemento HTML de la tarjeta del producto.
            
            if (!productCard) {
                console.error("Error: No se encontró la tarjeta de producto para el botón clickeado. Revisa la estructura HTML de tus productos.");
                return; // Detener la ejecución si no se encuentra la tarjeta
            }

            const productName = productCard.dataset.name;
            const productPrice = productCard.dataset.price;
            // Accedemos a data-paypal_url, que es el nombre del atributo en tu HTML.
            const paypalUrl = this.dataset.paypal_url; 

            console.log("Datos del producto extraídos:", { productName, productPrice, paypalUrl }); // Debugging log: Muestra los datos que se van a rellenar.

            document.getElementById('modal-product-title').textContent = productName;
            formProductName.value = productName;
            formProductPrice.value = productPrice;
            formPaypalUrl.value = paypalUrl;

            purchaseModal.classList.add('active'); // Añade la clase 'active' para mostrar el modal (asumiendo que CSS lo controla).
            console.log("Clase 'active' añadida al modal. Intentando mostrarlo."); // Debugging log: Indica que el modal debería estar visible.
        });
    });

    // Cierra el modal al hacer clic en el botón de cerrar
    closeButton.addEventListener('click', function() {
        console.log("Botón de cerrar modal clickeado.");
        purchaseModal.classList.remove('active');
        purchaseForm.reset(); // Opcional: Limpiar el formulario al cerrar el modal
    });

    // Cierra el modal al hacer clic fuera de su contenido
    window.addEventListener('click', function(event) {
        if (event.target === purchaseModal) {
            console.log("Clic fuera del modal detectado.");
            purchaseModal.classList.remove('active');
            purchaseForm.reset(); // Opcional: Limpiar el formulario al cerrar el modal
        }
    });

    /*
    // --- BLOQUE DE ENVÍO DE FORMULARIO COMENTADO/ELIMINADO ---
    // Este código ya NO es necesario porque el formulario HTML se envía directamente
    // a tu backend (a la ruta /process_purchase) mediante el atributo 'action' del formulario.
    // Si este bloque de código no está comentado o eliminado, interferirá con el nuevo flujo.

    // purchaseForm.addEventListener('submit', function(event) {
    //     event.preventDefault(); // Esto ya no es necesario si el formulario se envía directamente

    //     const formData = new FormData(purchaseForm);
    //     const data = {};
    //     for (let [key, value] of formData.entries()) {
    //         data[key] = value;
    //     }

    //     // Esta petición fetch ya no es necesaria y causaba el error CORS
    //     fetch('https://cast-sneakers-backend1.onrender.com/webhook/purchase', {
    //         method: 'POST',
    //         headers: {
    //             'Content-Type': 'application/json'
    //         },
    //         body: JSON.stringify(data)
    //     })
    //     .then(response => {
    //         console.log('Respuesta del backend:', response);
    //         if (response.ok) {
    //             console.log('Formulario enviado a Formspree con éxito!');
    //             const paypalRedirectUrl = formPaypalUrl.value;
    //             window.location.href = paypalRedirectUrl;

    //             purchaseModal.classList.remove('active');
    //             purchaseForm.reset();
    //         } else {
    //             response.json().then(data => {
    //                 console.error('Error al enviar el formulario. Detalles:', data);
    //                 alert('Hubo un error al procesar tu solicitud: ' + (data.error || 'Por favor, inténtalo de nuevo. Revisa la consola para más información.'));
    //             }).catch(() => {
    //                 console.error('Error al enviar el formulario. No se pudieron obtener detalles de la respuesta JSON.');
    //                 alert('Hubo un error al procesar tu solicitud. Por favor, inténtalo de nuevo. Revisa la consola para más información.');
    //             });
    //         }
    //     })
    //     .catch(error => {
    //         console.error('ERROR DE RED (fetch failed):', error);
    //         alert('¡ERROR DE RED! Por favor, verifica tu conexión a internet. Si el problema persiste, contacta con soporte. Revisa la consola del navegador (F12 > Consola) para más detalles.');
    //     });
    // });
    */
});