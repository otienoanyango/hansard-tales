/**
 * Hansard Tales - MP Search with Fuse.js
 * Implements fuzzy search for MPs by name, constituency, and party
 */

(function () {
    'use strict';

    // Search configuration
    const SEARCH_CONFIG = {
        minQueryLength: 2,
        maxResults: 10,
        fuseOptions: {
            keys: [
                { name: 'name', weight: 0.4 },
                { name: 'constituency', weight: 0.3 },
                { name: 'party', weight: 0.2 },
                { name: 'keywords', weight: 0.1 }
            ],
            threshold: 0.3,
            distance: 100,
            includeScore: true,
            useExtendedSearch: false
        }
    };

    let fuse = null;
    let searchData = null;
    let isLoading = false;

    /**
     * Load search index from JSON file
     */
    async function loadSearchIndex() {
        if (searchData) {
            return searchData;
        }

        if (isLoading) {
            // Wait for existing load to complete
            return new Promise((resolve) => {
                const checkInterval = setInterval(() => {
                    if (!isLoading) {
                        clearInterval(checkInterval);
                        resolve(searchData);
                    }
                }, 100);
            });
        }

        isLoading = true;

        try {
            const response = await fetch('/data/mp-search-index.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            searchData = await response.json();
            fuse = new Fuse(searchData, SEARCH_CONFIG.fuseOptions);
            return searchData;
        } catch (error) {
            console.error('Failed to load search index:', error);
            throw error;
        } finally {
            isLoading = false;
        }
    }

    /**
     * Perform search and return results
     */
    function performSearch(query) {
        if (!fuse || !searchData) {
            return [];
        }

        if (query.length < SEARCH_CONFIG.minQueryLength) {
            return [];
        }

        const results = fuse.search(query);
        return results.slice(0, SEARCH_CONFIG.maxResults);
    }

    /**
     * Format MP result as HTML
     */
    function formatResult(result) {
        const mp = result.item;
        const score = result.score;

        // Build constituency display
        const constituencyText = mp.constituency !== 'Nominated'
            ? mp.constituency
            : 'Nominated MP';

        // Build performance summary
        const stats = mp.current_term;
        const statsText = `${stats.statement_count} statements, ${stats.sessions_attended} sessions`;

        return `
            <a href="/mp/${mp.id}/" 
               class="block p-4 hover:bg-kenya-green-50 transition-colors border-b border-gray-200 last:border-b-0">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="font-semibold text-gray-900 text-lg mb-1">${escapeHtml(mp.name)}</h3>
                        <p class="text-sm text-gray-600 mb-1">
                            <span class="font-medium">${escapeHtml(constituencyText)}</span>
                            ${mp.party ? ` • ${escapeHtml(mp.party)}` : ''}
                        </p>
                        <p class="text-xs text-gray-500">${statsText}</p>
                    </div>
                    ${mp.photo_url ? `
                        <img src="${escapeHtml(mp.photo_url)}" 
                             alt="${escapeHtml(mp.name)}"
                             class="w-12 h-12 rounded-full border-2 border-black ml-4 object-cover"
                             onerror="this.style.display='none'">
                    ` : ''}
                </div>
            </a>
        `;
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Display search results
     */
    function displayResults(results, query, container) {
        if (results.length === 0) {
            container.innerHTML = `
                <div class="p-4 text-center text-gray-600">
                    <p class="font-semibold mb-2">No MPs found</p>
                    <p class="text-sm">Try searching by name, constituency, or party.</p>
                    <p class="text-sm mt-2">
                        Or <a href="/mps/" class="text-kenya-green-600 hover:text-kenya-green-800 underline">browse all MPs</a>.
                    </p>
                </div>
            `;
            return;
        }

        const resultsHtml = results.map(formatResult).join('');
        const countText = results.length === SEARCH_CONFIG.maxResults
            ? `Showing top ${results.length} results`
            : `Found ${results.length} result${results.length !== 1 ? 's' : ''}`;

        container.innerHTML = `
            <div class="p-2 bg-gray-50 border-b border-gray-200 text-xs text-gray-600 font-medium">
                ${countText} for "${escapeHtml(query)}"
            </div>
            ${resultsHtml}
        `;
    }

    /**
     * Display loading state
     */
    function displayLoading(container) {
        container.innerHTML = `
            <div class="p-4 text-center text-gray-600">
                <svg class="animate-spin h-6 w-6 mx-auto mb-2 text-kenya-green-600" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="text-sm">Loading search index...</p>
            </div>
        `;
    }

    /**
     * Display error state
     */
    function displayError(container, error) {
        container.innerHTML = `
            <div class="p-4 text-center text-red-600">
                <p class="font-semibold mb-2">Search unavailable</p>
                <p class="text-sm text-gray-600">Please try again later or <a href="/mps/" class="text-kenya-green-600 hover:text-kenya-green-800 underline">browse all MPs</a>.</p>
            </div>
        `;
        console.error('Search error:', error);
    }

    /**
     * Initialize search functionality
     */
    async function initSearch() {
        const searchInput = document.getElementById('mp-search');
        const searchResults = document.getElementById('search-results');

        if (!searchInput || !searchResults) {
            return;
        }

        let searchTimeout = null;

        // Handle search input
        searchInput.addEventListener('input', async function (e) {
            const query = e.target.value.trim();

            // Clear previous timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }

            // Hide results if query too short
            if (query.length < SEARCH_CONFIG.minQueryLength) {
                searchResults.classList.add('hidden');
                return;
            }

            // Show loading state
            searchResults.classList.remove('hidden');
            displayLoading(searchResults);

            // Debounce search
            searchTimeout = setTimeout(async () => {
                try {
                    // Load search index if not loaded
                    if (!searchData) {
                        await loadSearchIndex();
                    }

                    // Perform search
                    const results = performSearch(query);

                    // Display results
                    displayResults(results, query, searchResults);
                } catch (error) {
                    displayError(searchResults, error);
                }
            }, 300);
        });

        // Hide results when clicking outside
        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.add('hidden');
            }
        });

        // Show results when focusing on input with existing query
        searchInput.addEventListener('focus', function () {
            const query = searchInput.value.trim();
            if (query.length >= SEARCH_CONFIG.minQueryLength && searchResults.innerHTML) {
                searchResults.classList.remove('hidden');
            }
        });

        // Handle keyboard navigation
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                searchResults.classList.add('hidden');
                searchInput.blur();
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSearch);
    } else {
        initSearch();
    }

    // Export for testing
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            loadSearchIndex,
            performSearch,
            formatResult,
            escapeHtml
        };
    }
})();
