const viewMoreText = document.querySelector('.view-more');
const textContent = document.querySelector('.text');

viewMoreText.addEventListener('click', () => {
    textContent.classList.toggle('expandido');
    viewMoreText.textContent = textContent.classList.contains('expandido') ? 'Ver menos' : 'Ver más';
});