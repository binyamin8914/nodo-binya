// reuniones/static/reuniones/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    // Mostrar/Ocultar detalles al hacer clic en el título
    const toggles = document.querySelectorAll('h3');
    toggles.forEach(toggle => {
        const card = toggle.closest('.card');
        const content = Array.from(card.children).filter(child => child !== toggle);
        content.forEach(item => item.classList.add('collapsible-content'));

        toggle.addEventListener('click', () => {
            content.forEach(item => {
                if (item.classList.contains('hidden')) {
                    item.classList.remove('hidden');
                    item.classList.add('visible');
                } else {
                    item.classList.remove('visible');
                    item.classList.add('hidden');
                }
            });
        });

        // Inicialmente ocultar el contenido
        content.forEach(item => {
            item.classList.add('hidden');
        });
    });

    // Confirmación para botones "Eliminar"
    const deleteButtons = document.querySelectorAll('.button.delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            if (!confirm('¿Estás seguro de que deseas eliminar esta reunión?')) {
                e.preventDefault();
            }
        });
    });

    // Animación de botones
    const buttons = document.querySelectorAll('.button');
    buttons.forEach(button => {
        button.addEventListener('mousedown', () => {
            button.style.transform = 'scale(0.95)';
        });
        button.addEventListener('mouseup', () => {
            button.style.transform = 'scale(1)';
        });
    });
});