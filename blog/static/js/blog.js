
const searchInput = document.getElementById('search-input');
const resultsDiv = document.getElementById('results');

searchInput.addEventListener('input', function() {
    const query = searchInput.value;
    fetch(`/blog?q=${query}`)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newResults = doc.querySelector('#results').innerHTML;
            resultsDiv.innerHTML = newResults;
        })
        .catch(error => console.error('Error al buscar:', error));
});
