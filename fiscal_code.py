import re
from datetime import datetime

# Dictionary for month codes
MONTH_CODES = {
    1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'H',
    7: 'L', 8: 'M', 9: 'P', 10: 'R', 11: 'S', 12: 'T'
}

# Control character calculation table
ODD_CHAR_VALUES = {
    '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13,
    '6': 15, '7': 17, '8': 19, '9': 21, 'A': 1, 'B': 0,
    'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17,
    'I': 19, 'J': 21, 'K': 2, 'L': 4, 'M': 18, 'N': 20,
    'O': 11, 'P': 3, 'Q': 6, 'R': 8, 'S': 12, 'T': 14,
    'U': 16, 'V': 10, 'W': 22, 'X': 25, 'Y': 24, 'Z': 23
}

EVEN_CHAR_VALUES = {
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
    '6': 6, '7': 7, '8': 8, '9': 9, 'A': 0, 'B': 1,
    'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7,
    'I': 8, 'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13,
    'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19,
    'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25
}

REMAINDER_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Simplified dictionary for common locations
# In a real application, this would be a complete database of Italian city codes
COMUNE_CODES = {
    "ROMA": "H501",
    "MILANO": "F205",
    "NAPOLI": "F839",
    "TORINO": "L219",
    "PALERMO": "G273",
    "BOLOGNA": "A944",
    "FIRENZE": "D612",
    "GENOVA": "D969",
    "BARI": "A662",
    "CATANIA": "C351",
    "VENEZIA": "L736",
    "VERONA": "L781",
    "VARAZZE": "L675",
    # Add more cities as needed
    # For foreign countries:
    "ALBANIA": "Z100",
    "ALGERIA": "Z301",
    "ARGENTINA": "Z600",
    "BANGLADESH": "Z249",
    "BRAZIL": "Z602",
    "CAMEROON": "Z302",
    "CHINA": "Z210",
    "COLOMBIA": "Z604",
    "CÔTE D'IVOIRE": "Z317",
    "ECUADOR": "Z605",
    "EGYPT": "Z336",
    "ETHIOPIA": "Z315",
    "GAMBIA": "Z318",
    "GHANA": "Z321",
    "GUINEA": "Z324",
    "INDIA": "Z222",
    "IRAQ": "Z223",
    "LIBYA": "Z326",
    "MALI": "Z327",
    "MOROCCO": "Z330",
    "NIGERIA": "Z335",
    "PAKISTAN": "Z236",
    "PERU": "Z611",
    "SENEGAL": "Z343",
    "SOMALIA": "Z342",
    "SYRIA": "Z240",
    "TUNISIA": "Z352",
    "UKRAINE": "Z138",
    "UNITED KINGDOM": "Z114",
    "UNITED STATES": "Z404",
    "VENEZUELA": "Z614",
    # Default for other countries
    "ESTERO": "Z000"
}

def extract_consonants(s):
    """Extract consonants from a string"""
    return ''.join(c for c in s.upper() if c.isalpha() and c not in "AEIOU")

def extract_vowels(s):
    """Extract vowels from a string"""
    return ''.join(c for c in s.upper() if c.isalpha() and c in "AEIOU")

def calculate_fiscal_code(last_name, first_name, gender, birth_date, birth_place, country_code=None):
    """
    Calculate Italian fiscal code (codice fiscale)
    According to the Presidential Decree 605 of 29/09/1973
    This implementation closely follows the algorithm used by codicefiscaleonline.com
    """
    # Normalize input
    last_name = last_name.upper().strip().replace(' ', '')
    first_name = first_name.upper().strip().replace(' ', '')
    gender = gender.upper().strip()
    birth_place = birth_place.upper().strip()
    
    # 1. Last name part (3 characters)
    # Remove special characters and non-alphabetic chars from name
    last_name = ''.join(c for c in last_name if c.isalpha())
    
    # Extract consonants and vowels from last name
    last_name_consonants = extract_consonants(last_name)
    last_name_vowels = extract_vowels(last_name)
    
    # Get first 3 consonants, or fill with vowels if not enough consonants
    if len(last_name_consonants) >= 3:
        last_name_part = last_name_consonants[:3]
    else:
        last_name_part = last_name_consonants + last_name_vowels
        last_name_part = last_name_part[:3]
    
    # Fill with 'X' if still less than 3 characters
    last_name_part = last_name_part.ljust(3, 'X')
    
    # 2. First name part (3 characters)
    # Remove special characters and non-alphabetic chars from name
    first_name = ''.join(c for c in first_name if c.isalpha())
    
    # Extract consonants and vowels from first name
    first_name_consonants = extract_consonants(first_name)
    first_name_vowels = extract_vowels(first_name)
    
    # Special rule for first name: if there are at least 4 consonants,
    # use the 1st, 3rd, and 4th consonants
    if len(first_name_consonants) >= 4:
        first_name_part = first_name_consonants[0] + first_name_consonants[2:4]
    elif len(first_name_consonants) >= 3:
        first_name_part = first_name_consonants[:3]  # Use first 3 consonants
    else:
        first_name_part = first_name_consonants + first_name_vowels
        first_name_part = first_name_part[:3]
    
    # Fill with 'X' if still less than 3 characters
    first_name_part = first_name_part.ljust(3, 'X')
    
    # 3. Birth date and gender part (5 characters)
    # Last two digits of birth year
    year_part = str(birth_date.year)[-2:]
    
    # Letter for month - uses a specific letter for each month
    month_part = MONTH_CODES[birth_date.month]
    
    # Day + 40 for females
    if gender == 'F':
        day_part = str(birth_date.day + 40).zfill(2)
    else:
        day_part = str(birth_date.day).zfill(2)
    
    date_part = year_part + month_part + day_part
    
    # 4. Birth place code (4 characters)
    # Cerca il codice comune o paese estero nel dizionario
    birth_place_code = COMUNE_CODES.get(birth_place)
    
    # Normalizziamo il luogo di nascita per la ricerca
    normalized_birth_place = birth_place.replace('-', ' ').replace('\'', ' ').strip()
    
    # Se non è stato trovato con ricerca esatta, proviamo con una ricerca parziale
    if not birth_place_code:
        # Cerchiamo comuni/città in Italia
        for comune, code in COMUNE_CODES.items():
            # Solo per comuni italiani (non iniziano con Z)
            if not code.startswith('Z'):
                if normalized_birth_place in comune.upper() or comune.upper() in normalized_birth_place:
                    birth_place_code = code
                    break
    
    # Se ancora non trovato, potrebbe essere un paese estero
    if not birth_place_code:
        # Mappa di paesi comuni con i loro codici
        common_foreign_countries = {
            'MAROCCO': 'Z330',
            'ALBANIA': 'Z100', 
            'ROMANIA': 'Z129',
            'CINA': 'Z210',
            'TUNISIA': 'Z352',
            'PAKISTAN': 'Z236',
            'NIGERIA': 'Z335',
            'BANGLADESH': 'Z249',
            'UCRAINA': 'Z138',
            'SENEGAL': 'Z343',
            'INDIA': 'Z222',
            'EGITTO': 'Z336',
            'PERU': 'Z611',
            'FILIPPINE': 'Z216'
        }
        
        # Cerchiamo se il luogo di nascita contiene o è contenuto in un paese comune
        for country, code in common_foreign_countries.items():
            if country in normalized_birth_place.upper() or normalized_birth_place.upper() in country:
                birth_place_code = code
                break
        
        # Se ancora non trovato, cerchiamo in tutti i paesi esteri nel dizionario
        if not birth_place_code:
            for comune, code in COMUNE_CODES.items():
                if code.startswith('Z'):  # Solo per paesi esteri (iniziano con Z)
                    if normalized_birth_place in comune.upper() or comune.upper() in normalized_birth_place:
                        birth_place_code = code
                        break
        
        # Se ancora non trovato, controlliamo parole chiave per continenti
        if not birth_place_code:
            continent_keywords = {
                'AFRICA': 'Z301',  # Generico Africa
                'ASIA': 'Z201',    # Generico Asia
                'EUROPA': 'Z100',  # Generico Europa
                'AMERICA': 'Z401', # Generico America
                'STATI UNITI': 'Z404',  # USA
                'USA': 'Z404'      # USA
            }
            
            for keyword, code in continent_keywords.items():
                if keyword in normalized_birth_place.upper():
                    birth_place_code = code
                    break
        
        # Se ancora non trovato, usa Z000 (generico estero)
        if not birth_place_code:
            birth_place_code = "Z000"
    
    # 5. Combine parts without check digit
    fiscal_code = last_name_part + first_name_part + date_part + birth_place_code
    
    # 6. Calculate check digit
    total = 0
    for i, char in enumerate(fiscal_code):
        if (i + 1) % 2 == 0:  # Even position
            total += EVEN_CHAR_VALUES[char]
        else:  # Odd position
            total += ODD_CHAR_VALUES[char]
    
    check_digit = REMAINDER_CHARS[total % 26]
    
    # 7. Add check digit
    fiscal_code += check_digit
    
    return fiscal_code
