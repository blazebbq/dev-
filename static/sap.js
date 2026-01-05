// SAP-style UI JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // Update server time
    updateServerTime();
    setInterval(updateServerTime, 1000);
    
    // Setup context selectors
    setupContextSelectors();
    
    // Setup command field
    setupCommandField();
    
    // Setup Enter key validation
    setupEnterValidation();
});

function updateServerTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    const elem = document.getElementById('serverTime');
    if (elem) {
        elem.textContent = timeStr;
    }
}

function setupContextSelectors() {
    const plantSelector = document.getElementById('plantSelector');
    const slocSelector = document.getElementById('slocSelector');
    
    if (plantSelector) {
        plantSelector.addEventListener('change', () => {
            const plant = plantSelector.value;
            document.getElementById('currentPlant').textContent = plant;
            // Store in session storage
            sessionStorage.setItem('currentPlant', plant);
            // Trigger plant change event
            document.dispatchEvent(new CustomEvent('plantChanged', { detail: { plant } }));
        });
        
        // Load from session storage
        const savedPlant = sessionStorage.getItem('currentPlant');
        if (savedPlant) {
            plantSelector.value = savedPlant;
            document.getElementById('currentPlant').textContent = savedPlant;
        }
    }
    
    if (slocSelector) {
        slocSelector.addEventListener('change', () => {
            const sloc = slocSelector.value;
            document.getElementById('currentSloc').textContent = sloc;
            sessionStorage.setItem('currentSloc', sloc);
            document.dispatchEvent(new CustomEvent('slocChanged', { detail: { sloc } }));
        });
        
        const savedSloc = sessionStorage.getItem('currentSloc');
        if (savedSloc) {
            slocSelector.value = savedSloc;
            document.getElementById('currentSloc').textContent = savedSloc;
        }
    }
}

function setupCommandField() {
    const commandField = document.getElementById('commandField');
    if (commandField) {
        commandField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                let tcode = commandField.value.trim().toUpperCase();
                
                // Strip /n or /o prefix
                tcode = tcode.replace(/^\/[NO]/, '');
                
                if (tcode) {
                    // Navigate to transaction
                    window.location.href = `/tcode/${tcode.toLowerCase()}`;
                }
            }
        });
    }
}

function setupEnterValidation() {
    // On forms with check/post buttons, Enter should trigger check, not post
    const forms = document.querySelectorAll('.sap-form');
    forms.forEach(form => {
        form.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                
                // Look for check button
                const checkBtn = form.querySelector('[data-action="check"]');
                if (checkBtn) {
                    checkBtn.click();
                }
            }
        });
    });
}

function showStatusMessage(message, type = 'info') {
    const statusElem = document.getElementById('statusMessage');
    if (statusElem) {
        statusElem.innerHTML = `<span class="sap-status-${type}">${message}</span>`;
        
        // Auto-clear after 10 seconds
        setTimeout(() => {
            if (statusElem.innerHTML.includes(message)) {
                statusElem.innerHTML = 'Ready';
            }
        }, 10000);
    }
}

function getCurrentPlant() {
    return document.getElementById('currentPlant')?.textContent || '1000';
}

function getCurrentSloc() {
    return document.getElementById('currentSloc')?.textContent || '0001';
}

// Auto-fill plant/sloc from context
function autofillContext() {
    const plantInputs = document.querySelectorAll('[name="plant_code"], [name="plant"]');
    const slocInputs = document.querySelectorAll('[name="sloc_to_code"], [name="sloc_from_code"], [name="sloc_code"]');
    
    plantInputs.forEach(input => {
        if (!input.value) {
            input.value = getCurrentPlant();
        }
    });
    
    slocInputs.forEach(input => {
        if (!input.value && input.name === 'sloc_to_code') {
            input.value = getCurrentSloc();
        }
    });
}

// Call autofill when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autofillContext);
} else {
    autofillContext();
}

// Material search helper
async function searchMaterial(query) {
    if (query.length < 2) return [];
    
    try {
        const response = await fetch(`/api/products?search=${encodeURIComponent(query)}`);
        if (response.ok) {
            const materials = await response.json();
            return materials.slice(0, 10);
        }
    } catch (error) {
        console.error('Error searching materials:', error);
    }
    return [];
}

// Setup autocomplete for material fields
function setupMaterialAutocomplete(inputElement) {
    let timeout = null;
    let currentResults = [];
    
    // Create results container
    const resultsDiv = document.createElement('div');
    resultsDiv.className = 'sap-autocomplete-results';
    resultsDiv.style.cssText = 'position:absolute; background:#fff; border:1px solid #999; max-height:200px; overflow-y:auto; z-index:1000; display:none;';
    inputElement.parentElement.style.position = 'relative';
    inputElement.parentElement.appendChild(resultsDiv);
    
    inputElement.addEventListener('input', (e) => {
        clearTimeout(timeout);
        const query = e.target.value;
        
        if (query.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }
        
        timeout = setTimeout(async () => {
            currentResults = await searchMaterial(query);
            
            if (currentResults.length > 0) {
                resultsDiv.innerHTML = currentResults.map(m => 
                    `<div class="sap-autocomplete-item" style="padding:6px 10px; cursor:pointer; border-bottom:1px solid #eee;" 
                          data-sku="${m.sku}" data-name="${m.name}">
                        <strong>${m.sku}</strong> - ${m.name}
                    </div>`
                ).join('');
                resultsDiv.style.display = 'block';
                
                // Add click handlers
                resultsDiv.querySelectorAll('.sap-autocomplete-item').forEach(item => {
                    item.addEventListener('click', () => {
                        inputElement.value = item.dataset.sku;
                        resultsDiv.style.display = 'none';
                        
                        // Trigger change event
                        inputElement.dispatchEvent(new Event('change', { bubbles: true }));
                    });
                    
                    item.addEventListener('mouseenter', () => {
                        item.style.background = '#ffffcc';
                    });
                    
                    item.addEventListener('mouseleave', () => {
                        item.style.background = '';
                    });
                });
            } else {
                resultsDiv.style.display = 'none';
            }
        }, 300);
    });
    
    // Close on blur (with delay to allow clicks)
    inputElement.addEventListener('blur', () => {
        setTimeout(() => {
            resultsDiv.style.display = 'none';
        }, 200);
    });
}

// Initialize autocomplete for all material inputs on page
document.addEventListener('DOMContentLoaded', () => {
    const materialInputs = document.querySelectorAll('[name="material_sku"], [name="material"]');
    materialInputs.forEach(input => {
        setupMaterialAutocomplete(input);
    });
});
