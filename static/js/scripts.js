// Ancora CAS Management System Scripts

document.addEventListener('DOMContentLoaded', function() {
    // Initialize custom field counter
    let customFieldCount = 0;
    
    // Add custom field button handler
    const addCustomFieldBtn = document.getElementById('add-custom-field');
    if (addCustomFieldBtn) {
        addCustomFieldBtn.addEventListener('click', function() {
            addCustomField();
        });
    }
    
    // Initialize DataTables
    const guestsTable = document.getElementById('guests-table');
    if (guestsTable) {
        $(guestsTable).DataTable({
            responsive: true,
            language: {
                search: "Cerca:",
                lengthMenu: "Mostra _MENU_ righe per pagina",
                info: "Visualizzazione da _START_ a _END_ di _TOTAL_ righe",
                infoEmpty: "Nessun risultato disponibile",
                infoFiltered: "(filtrato da _MAX_ righe totali)",
                zeroRecords: "Nessun risultato trovato",
                paginate: {
                    first: "Primo",
                    last: "Ultimo",
                    next: "Successivo",
                    previous: "Precedente"
                }
            }
        });
    }
    
    // Calculate fiscal code button handler
    const calculateCfBtn = document.getElementById('calculate-cf-btn');
    if (calculateCfBtn) {
        calculateCfBtn.addEventListener('click', function() {
            calculateFiscalCode();
        });
    }
    
    // Setup date display fields
    initializeDateFields();
    
    // Permit date change handler - auto calculate expiry
    const permitDateInput = document.getElementById('permit_date');
    if (permitDateInput) {
        permitDateInput.addEventListener('change', function() {
            calculatePermitExpiry();
            updateDateDisplay('permit_date');
        });
    }
    
    // Family relation selection handler
    initializeFamilyRelationSelector();
    
    // Function to add a new custom field
    function addCustomField() {
        customFieldCount++;
        
        const customFieldsContainer = document.getElementById('custom-fields-container');
        if (!customFieldsContainer) return; // Exit if container not found
        
        const newRow = document.createElement('div');
        newRow.classList.add('row', 'custom-field-row');
        newRow.innerHTML = `
            <div class="col-md-5">
                <input type="text" class="form-control" name="custom_field_name_${customFieldCount}" placeholder="Nome campo">
            </div>
            <div class="col-md-5">
                <input type="text" class="form-control" name="custom_field_${customFieldCount}" placeholder="Valore">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-danger btn-remove-field" data-field-id="${customFieldCount}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        customFieldsContainer.appendChild(newRow);
        
        // Add remove button handler
        const removeBtn = newRow.querySelector('.btn-remove-field');
        removeBtn.addEventListener('click', function() {
            removeCustomField(this);
        });
    }
    
    // Function to remove a custom field
    function removeCustomField(button) {
        const fieldId = button.getAttribute('data-field-id');
        const fieldRow = button.closest('.custom-field-row');
        fieldRow.remove();
    }
    
    // Function to calculate permit expiry date
    function calculatePermitExpiry() {
        const permitDateInput = document.getElementById('permit_date');
        const permitExpiryInput = document.getElementById('permit_expiry');
        const permitExpiryDisplay = document.getElementById('permit_expiry_display');
        
        if (permitDateInput && permitExpiryInput && permitDateInput.value) {
            const permitDate = new Date(permitDateInput.value);
            const expiryDate = new Date(permitDate);
            expiryDate.setMonth(expiryDate.getMonth() + 6);
            
            // Format date as YYYY-MM-DD for input field
            const formattedDate = expiryDate.toISOString().split('T')[0];
            permitExpiryInput.value = formattedDate;
            
            // Format date as DD/MM/YYYY for display
            if (permitExpiryDisplay) {
                const day = String(expiryDate.getDate()).padStart(2, '0');
                const month = String(expiryDate.getMonth() + 1).padStart(2, '0');
                const year = expiryDate.getFullYear();
                permitExpiryDisplay.textContent = `${day}/${month}/${year}`;
            }
        } else if (permitExpiryInput) {
            permitExpiryInput.value = '';
            if (permitExpiryDisplay) {
                permitExpiryDisplay.textContent = '';
            }
        }
    }
    
    // Function to initialize family relation selector
    function initializeFamilyRelationSelector() {
        const familyRelationsContainer = document.getElementById('family-relations-container');
        const guestSelect = document.getElementById('related-guest');
        const relationSelect = document.getElementById('relation-type');
        const addRelationBtn = document.getElementById('add-relation-btn');
        
        if (addRelationBtn) {
            addRelationBtn.addEventListener('click', function() {
                const guestOption = guestSelect.options[guestSelect.selectedIndex];
                const relationOption = relationSelect.options[relationSelect.selectedIndex];
                
                if (guestOption.value && relationOption.value) {
                    const relation = relationOption.text + ' di ' + guestOption.text;
                    
                    // Add to textarea
                    const textarea = document.getElementById('family_relations');
                    if (textarea.value) {
                        textarea.value += '\n' + relation;
                    } else {
                        textarea.value = relation;
                    }
                }
            });
        }
    }
    
    // Initialize existing custom fields in edit mode
    const existingCustomFields = document.querySelectorAll('.existing-custom-field');
    if (existingCustomFields.length > 0) {
        existingCustomFields.forEach(function(field, index) {
            customFieldCount = Math.max(customFieldCount, index + 1);
            
            // Add remove button handler
            const removeBtn = field.querySelector('.btn-remove-field');
            if (removeBtn) {
                removeBtn.addEventListener('click', function() {
                    removeCustomField(this);
                });
            }
        });
    }
    
    // Date range validation for export form
    const exportForm = document.getElementById('export-form');
    if (exportForm) {
        exportForm.addEventListener('submit', function(event) {
            const dateFrom = document.getElementById('entry_date_from').value;
            const dateTo = document.getElementById('entry_date_to').value;
            
            if (dateFrom && dateTo) {
                if (new Date(dateFrom) > new Date(dateTo)) {
                    event.preventDefault();
                    alert('La data di inizio deve essere precedente alla data di fine.');
                }
            }
        });
    }
    
    // Toggle sidebar on mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.getElementById('sidebar').classList.toggle('d-none');
        });
    }
    
    // Automatically close alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert && typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);
});

// Function to confirm delete
function confirmDelete(guestId, guestName) {
    if (confirm(`Sei sicuro di voler eliminare l'ospite ${guestName}?`)) {
        document.getElementById(`delete-form-${guestId}`).submit();
    }
}

// Function to calculate fiscal code (this will call the backend API)
function calculateFiscalCode() {
    const lastName = document.getElementById('last_name').value;
    const firstName = document.getElementById('first_name').value;
    const gender = document.getElementById('gender').value;
    const birthDate = document.getElementById('birth_date').value;
    const birthPlace = document.getElementById('birth_place').value;
    
    if (!lastName || !firstName || !gender || !birthDate || !birthPlace) {
        alert('Per calcolare il codice fiscale compilare: cognome, nome, sesso, data e luogo di nascita.');
        return;
    }
    
    // Update the date display field
    updateDateDisplay('birth_date');
    
    // Call backend API to calculate fiscal code
    fetch('/calculate_fiscal_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            last_name: lastName,
            first_name: firstName,
            gender: gender,
            birth_date: birthDate,
            birth_place: birthPlace
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Errore: ' + data.error);
        } else {
            document.getElementById('fiscal_code').value = data.fiscal_code;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Errore durante il calcolo del codice fiscale.');
    });
}

// Function to update the displayed date in dd/mm/yyyy format
function updateDateDisplay(inputId) {
    const dateInput = document.getElementById(inputId);
    const displayField = document.getElementById(inputId + '_display');
    
    if (dateInput && displayField && dateInput.value) {
        // Parse the date in YYYY-MM-DD format (HTML input format)
        const parts = dateInput.value.split('-');
        if (parts.length === 3) {
            const year = parts[0];
            const month = parts[1];
            const day = parts[2];
            
            // Display in Italian format dd/mm/yyyy
            displayField.textContent = `${day}/${month}/${year}`;
        }
    }
}

// Function to initialize all date fields
function initializeDateFields() {
    // List of all date input fields
    const dateFields = ['birth_date', 'permit_date', 'permit_expiry', 'health_card_expiry', 'entry_date'];
    
    // For each date field, add change listener and update display initially
    dateFields.forEach(fieldId => {
        const input = document.getElementById(fieldId);
        if (input) {
            // Update initial display
            updateDateDisplay(fieldId);
            
            // Add change listener
            input.addEventListener('change', function() {
                updateDateDisplay(fieldId);
            });
        }
    });
}
