document.addEventListener('DOMContentLoaded', function () {

    var sortSelect = document.getElementById('sortOptions');

    // Event listener for sort option changes
    sortSelect.addEventListener('change', function () {
        // Perform the search again with the new sort option
        search();
    });


    // Event listener for search button click
    document.getElementById('searchButton').addEventListener('click', function () {
        search();
    });

    // Function to send search request
    function sendSearchRequest(url, data) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error searching:', error);
            throw error;
        });
    }

    // Function to perform search
    function search() {
        var searchInput = document.getElementById('searchInput').value;
        var sortOption = document.getElementById('sortOptions').value;
        var data = {
            search_text: searchInput,
            sort_by: sortOption
        };

        sendSearchRequest('/search-meeting', data)
        .then(results => {
            console.log('Search results:', results);

            const searchResultsContainer = document.querySelector('#search-results');
searchResultsContainer.innerHTML = '';

            // Append "Back to Dashboard" button if it doesn't exist
            let backToDashboardButton = document.getElementById('backToDashboard');
            if (!backToDashboardButton) {
                backToDashboardButton = document.createElement('button');
                backToDashboardButton.id = 'backToDashboard';
                backToDashboardButton.classList.add('btn', 'btn-primary', 'mt-2');
                backToDashboardButton.innerText = 'Back to Dashboard';
                backToDashboardButton.onclick = function () {
                    window.location.href = '/dashboard';
                };
                searchResultsContainer.prepend(backToDashboardButton);
            }

            if (results.length === 0) {
                searchResultsContainer.innerHTML += '<p>No results found.</p>';
            } else {
                results.forEach(result => {
                    const resultCard = document.createElement('div');
                    resultCard.classList.add('card', 'mb-3');
                    resultCard.innerHTML = `
                        <div class="card-body">
                          <h5 class="card-title">${highlightSearchTerm(result.Meeting_Name, data.search_text)}</h5>
                          <h6 class="card-subtitle mb-2 text-muted">${highlightSearchTerm(result.Date, data.search_text)}</h6>
                          <p class="card-text">${highlightSearchTerm(result.Summary, data.search_text)}</p>
                        </div>
                      `;
                    searchResultsContainer.appendChild(resultCard);
                });
            }

            // Optionally clear the search input here if desired
            document.getElementById('searchInput').value = '';
        })
        .catch(error => {
            const errorMessageDiv = document.getElementById('error-message');
            if (errorMessageDiv) {
                errorMessageDiv.innerText = 'An error occurred during the search. Please try again.';
                errorMessageDiv.style.display = 'none';
            }
        });
    }

    // Highlight search term within text
    function highlightSearchTerm(text, searchTerm) {
        const regex = new RegExp(searchTerm, 'gi');
        return text.replace(regex, match => `<span class="highlight">${match}</span>`);
    }

    // Event listeners for HTMX requests
    document.addEventListener('htmx:configRequest', (event) => {
        console.log('HTMX request being configured:', event.detail);
    });

    document.addEventListener('htmx:afterRequest', (event) => {
        console.log('HTMX request finished:', event.detail);
    });

    document.addEventListener('htmx:responseError', (event) => {
        console.error('HTMX request error:', event.detail);
    });
});
