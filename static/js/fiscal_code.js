// Italian Fiscal Code Calculator Client-Side
// This is a client-side implementation for validation and preview

// Dictionary for month codes
const MONTH_CODES = {
    1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'H',
    7: 'L', 8: 'M', 9: 'P', 10: 'R', 11: 'S', 12: 'T'
};

// Function to extract consonants from a string
function extractConsonants(str) {
    return str.toUpperCase().replace(/[^BCDFGHJKLMNPQRSTVWXYZ]/g, '');
}

// Function to extract vowels from a string
function extractVowels(str) {
    return str.toUpperCase().replace(/[^AEIOU]/g, '');
}

// Client-side fiscal code calculation preview
// Note: This is for preview only. The actual calculation is done on the server
function previewFiscalCode() {
    const lastName = document.getElementById('last_name').value;
    const firstName = document.getElementById('first_name').value;
    const gender = document.getElementById('gender').value;
    const birthDateInput = document.getElementById('birth_date').value;
    
    if (!lastName || !firstName || !gender || !birthDateInput) {
        return '';
    }
    
    // Process birth date
    const birthDate = new Date(birthDateInput);
    
    // 1. Last name part (3 characters - usually 1st, 2nd, 3rd consonants)
    let lastNameConsonants = extractConsonants(lastName);
    let lastNameVowels = extractVowels(lastName);
    
    let lastNamePart;
    if (lastNameConsonants.length >= 3) {
        lastNamePart = lastNameConsonants.substring(0, 3);
    } else {
        lastNamePart = lastNameConsonants + lastNameVowels;
        lastNamePart = lastNamePart.substring(0, 3);
    }
    
    // Fill with 'X' if still less than 3 characters
    while (lastNamePart.length < 3) {
        lastNamePart += 'X';
    }
    
    // 2. First name part (3 characters - usually 1st, 3rd, 4th consonants)
    let firstNameConsonants = extractConsonants(firstName);
    let firstNameVowels = extractVowels(firstName);
    
    let firstNamePart;
    if (firstNameConsonants.length >= 4) {
        // Special rule: use 1st, 3rd and 4th consonant
        firstNamePart = firstNameConsonants.charAt(0) + firstNameConsonants.substring(2, 4);
    } else if (firstNameConsonants.length == 3) {
        firstNamePart = firstNameConsonants.substring(0, 3); // Use all three consonants
    } else {
        firstNamePart = firstNameConsonants + firstNameVowels;
        firstNamePart = firstNamePart.substring(0, 3);
    }
    
    // Fill with 'X' if still less than 3 characters
    while (firstNamePart.length < 3) {
        firstNamePart += 'X';
    }
    
    // 3. Birth date and gender part (5 characters)
    // Last two digits of birth year
    const yearPart = birthDate.getFullYear().toString().substring(2);
    
    // Letter for month
    const monthPart = MONTH_CODES[birthDate.getMonth() + 1];
    
    // Day + 40 for females
    let dayPart;
    if (gender === 'F') {
        dayPart = (birthDate.getDate() + 40).toString().padStart(2, '0');
    } else {
        dayPart = birthDate.getDate().toString().padStart(2, '0');
    }
    
    const datePart = yearPart + monthPart + dayPart;
    
    // 4. Return partial code (without place code and check digit)
    // The full calculation requires city codes and will be done server-side
    return lastNamePart + firstNamePart + datePart + '????' + '?';
}

// Add event listeners to form fields
document.addEventListener('DOMContentLoaded', function() {
    const inputs = ['last_name', 'first_name', 'gender', 'birth_date'];
    
    inputs.forEach(function(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', function() {
                const preview = previewFiscalCode();
                const fiscalInput = document.getElementById('fiscal_code');
                
                // Only show preview if it's not set yet or if it was a preview before
                if (fiscalInput && (!fiscalInput.value || fiscalInput.value.includes('?'))) {
                    fiscalInput.value = preview;
                }
            });
        }
    });
});
