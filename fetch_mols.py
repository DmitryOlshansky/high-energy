import os
import time
import urllib.parse
import requests

# List of all 34 molecules from Table 1
# Format: ("Chemical Name for Search", "Code Designation for Filename")
molecules = [
    ("1,3-Dinitrobenzene", "1,3-DNB"),
    ("1,4-Dinitrobenzene", "1,4-DNB"),
    ("1,3,5-Trinitrobenzene", "TNB"),
    ("2,2',4,4',6,6'-Hexanitrobiphenyl", "HNB"),
    ("NONA", "NONA"),
    ("2,4,6-tris(2,4,6-Trinitrophenyl)-1,3,5-triazine", "TPT"),
    ("1,5-Dinitronaphthalene", "1,5-DNN"),
    ("1,8-Dinitronaphthalene", "1,8-DNN"),
    ("1,4,5-Trinitronaphthalene", "TNN"),
    ("1,4,5,8-Tetranitronaphthalene", "TENN"),
    ("BTX", "BTX"),
    ("1-Methyl-2,4,6-trinitrobenzene", "TNT"),
    ("1,3-Dimethyl-2,4,6-trinitrobenzene", "TNX"),
    ("1,3,5-Trimethyl-2,4,6-trinitrobenzene", "TNMs"),
    ("TNA", "TNA"),
    ("2,4,6-Trinitrobenzoic acid", "TNBA"),
    ("1-Hydroxy-2,4,6-trinitrobenzene", "PA"),     # 'Hydroxi' fixed for API search
    ("1,3-Dihydroxy-2,4,6-trinitrobenzene", "TNR"), # 'Dihydroxi' fixed for API search
    ("1-Amino-2,4,6-trinitrobenzene", "PAM"),
    ("1,3-Diamino-2,4,6-trinitrobenzene", "DATB"),
    ("1,3,5-Triamino-2,4,6-trinitrobenzene", "TATB"),
    ("2,2',4,4',6,6'-Hexanitrodiphenylamine", "DPA"),
    ("2,2',4,4',6,6'-Hexanitrooxanilide", "HNO"),
    ("TMPM", "TMPM"),
    ("PYX", "PYX"),
    ("1,3,7,9-Tetranitrophenothiazine-5,5-dioxide", "TNPTD"),
    ("1,3,7,9-Tetranitrophenoxazine", "TENPO"),
    ("DIPS", "DIPS"),
    ("DMDIPS", "DMDIPS"),
    ("DIPSO", "DIPSO"),
    ("2,2',4,4',6,6'-Hexanitrodiphenylmethane", "DPM"),
    ("1,2-bis(2,4,6-Trinitrophenyl)ethane", "DPE"),
    ("3,3'-Dimethyl-2,2',4,4',6,6'-hexanitrobiphenyl", "BITNT"),
    ("2,2',4,4',6,6'-Hexanitrostilbene", "HNS")
]

# Create output directory
output_dir = "mol_files"
os.makedirs(output_dir, exist_ok=True)

print(f"Starting download of {len(molecules)} MOL files...\n")

for chem_name, code in molecules:
    # URL encode the chemical name
    encoded_name = urllib.parse.quote(chem_name)
    
    # PubChem API endpoint for 2D SDF/MOL files
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/SDF"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Use the Code Designation for the file name
            filepath = os.path.join(output_dir, f"{code}.mol")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"[SUCCESS] Downloaded: {code}.mol ({chem_name})")
        else:
            print(f"[FAILED] Could not resolve: {chem_name} (HTTP {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error for {chem_name}: {e}")
        
    # Respect API rate limits (PubChem allows ~5 requests per second)
    time.sleep(0.4)

print("\nFinished process.")
