const sliderContainer = document.querySelector('.slider-container');
const slides = document.querySelectorAll('.slide');
const prevButton = document.querySelector('.slider-btn.prev');
const nextButton = document.querySelector('.slider-btn.next');

let currentIndex = 0;
let startX = 0;
let currentTranslate = 0;
let prevTranslate = 0;
let isDragging = false;

// Actualiza la posición del slider
function updateSliderPosition() {
    const offset = -currentIndex * 100; // Mueve el slider por cada slide
    sliderContainer.style.transform = `translateX(${offset}%)`;
}

// Función para touch
function startTouch(e) {
    isDragging = true;
    startX = e.touches[0].clientX; // Registro del punto inicial
    prevTranslate = currentTranslate; // Mantén la posición previa
}

// Función para mover el slider durante el touch
function moveTouch(e) {
    if (!isDragging) return;

    const currentX = e.touches[0].clientX;
    const diff = currentX - startX;
    currentTranslate = prevTranslate + diff;

    // Mover el contenedor mientras el usuario desliza
    sliderContainer.style.transform = `translateX(${currentTranslate}px)`;
}

// Función para finalizar el touch
function endTouch() {
    isDragging = false;

    const movedBy = currentTranslate - prevTranslate;

    if (movedBy < -50) {
        // Avanzar al siguiente slide
        if (currentIndex < slides.length - 1) {
            currentIndex++;
        } else {
            currentIndex = 0; // Regresar al primer slide si es el último
        }
    } else if (movedBy > 50) {
        // Retroceder al slide anterior
        if (currentIndex > 0) {
            currentIndex--;
        } else {
            currentIndex = slides.length - 1; // Ir al ultimo slide si está en el primero
        }
    }


    // Restaura la posición a un slide fijo
    updateSliderPosition();
}

// slider Touch
sliderContainer.addEventListener('touchstart', startTouch);
sliderContainer.addEventListener('touchmove', moveTouch);
sliderContainer.addEventListener('touchend', endTouch);


// siguiente
nextButton.addEventListener('click', () => {
    if (currentIndex < slides.length - 1) {
        currentIndex++;
    } else {
        currentIndex = 0; //volver al primer
    }
    updateSliderPosition();
});

// anterior
prevButton.addEventListener('click', () => {
    if (currentIndex > 0) {
        currentIndex--;
    } else {
        currentIndex = slides.length - 1; // Go to the last slide
    }
    updateSliderPosition();
});



//POPUP
const popup = document.getElementById('popup');
const closePopupBtn = document.getElementById('cerrarpopup');
let popup_visto = false;
window.addEventListener('scroll', () => {
    if (!popup_visto && window.scrollY > 450) { 
        popup.style.display = 'flex'; // mostrar 
        popup_visto = true; // marcar que ya se mostro
    }
});

// Cerrar el popup
closePopupBtn.addEventListener('click', () => {
    popup.classList.add('closing');
    popup.addEventListener('animationend', () => {
        popup.style.display = 'none'; // Oculta el popup después de la animación
        popup.classList.remove('closing'); // 
    }, { once: true }); 
});
