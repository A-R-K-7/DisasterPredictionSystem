document.addEventListener('DOMContentLoaded', function() {
    // Find all location input containers
    const locationInputs = document.querySelectorAll('.location-input-container input');
    
    locationInputs.forEach(function(locationInput) {
        const inputId = locationInput.id;
        const fieldName = inputId.replace('id_', '');
        const suggestionsContainer = document.getElementById(`${fieldName}-suggestions`);
        const loadingIndicator = document.getElementById(`${fieldName}-loading`);
        
        if (!suggestionsContainer || !loadingIndicator) return;
        
        let debounceTimer;
        
        // Function to fetch location suggestions
        async function getLocationSuggestions(query) {
            if (!query || query.length < 3) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            loadingIndicator.style.display = 'block';
            
            try {
                const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`);
                const data = await response.json();
                
                // Clear previous suggestions
                suggestionsContainer.innerHTML = '';
                
                if (data.length > 0) {
                    data.forEach(place => {
                        const suggestion = document.createElement('div');
                        suggestion.className = 'suggestion-item';
                        suggestion.textContent = place.display_name;
                        
                        suggestion.addEventListener('click', function() {
                            // Fill the form fields with selected location
                            locationInput.value = place.display_name;
                            
                            // Find lat/lon fields
                            const formRoot = locationInput.closest('form');
                            const latField = formRoot.querySelector('#id_latitude');
                            const lonField = formRoot.querySelector('#id_longitude');
                            
                            if (latField && lonField) {
                                latField.value = place.lat;
                                lonField.value = place.lon;
                            }
                            
                            // Hide suggestions
                            suggestionsContainer.style.display = 'none';
                        });
                        
                        suggestionsContainer.appendChild(suggestion);
                    });
                    
                    suggestionsContainer.style.display = 'block';
                } else {
                    suggestionsContainer.style.display = 'none';
                }
            } catch (error) {
                console.error('Error fetching location suggestions:', error);
            } finally {
                loadingIndicator.style.display = 'none';
            }
        }
        
        // Add input event with debounce
        locationInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                getLocationSuggestions(this.value);
            }, 500); // 500ms debounce
        });
        
        // Close suggestions when clicking outside
        document.addEventListener('click', function(event) {
            if (!locationInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
                suggestionsContainer.style.display = 'none';
            }
        });
        
        // Close suggestions when pressing escape
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                suggestionsContainer.style.display = 'none';
            }
        });
    });
}); 