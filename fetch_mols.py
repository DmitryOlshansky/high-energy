import os
import requests
import time

# Dictionary of molecules. 
# Keys are the filenames you want to save.
# Values are either the common name, IUPAC name, or PubChem CID for accurate fetching.
molecules = {
    "DIGEN": "1-Nitro-1-azaethylene", # Closest standard match for 1-Nitro-1-azaethylene
    "EDNA": "1,4-dinitro-1,4-diazabutane",
    "OCPX": "2,4-Dinitro-2,4-diazapentane",
    "ORDX": "2,4,6-Trinitro-2,4,6-triazaheptane",
    "OHMX": "2,4,6,8-Tetranitro-2,4,6,8-tetraazanonane",
    "AcAn": "1,9-diacetoxy-2,4,6,8-tetranitro-2,4,6,8-tetraazanonane",
    "TETROGEN": "1,3-Dinitro-1,3-diazacyclobutane",
    "TNAZ": "1,3,3-Trinitroazetidine",
    "CPX": "1,3-dinitroimidazolidine", # 1,3-Dinitro-1,3-diazacyclopentane
    "DNDC": "1,4-dinitropiperazine", # 1,4-Dinitro-1,4-diazacyclohexane
    "RDX": "RDX",
    "DPT": "1,3-Endomethylene-3,7-dinitro-1,3,5,7-tetraazacyclooctane", # 1,3-Endomethylene-3,7-dinitro-1,3,5,7-tetraazacyclooctane
    "HMX": "HMX",
    "DECAGEN": "DECAGEN",
    "TEX": "TEX",
    "HNIW": "CL-20", # Common identifier for Hexanitrohexaazaisowurtzitane
    "DMNO": "2,5-Dinitro-2,5-diazahexane-3,4-dione",
    "TETRYL": "Tetryl"
}

OUTPUT_DIR = "mol_files"

def fetch_mol_file(identifier, filename):
    """Fetches the 3D or 2D SDF/MOL file from PubChem."""
    # Try fetching by name first
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{identifier}/SDF"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        filepath = os.path.join(OUTPUT_DIR, f"{filename}.mol")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"[SUCCESS] Fetched MOL for {filename} ({identifier})")
    else:
        print(f"[FAILED] Could not find {filename} ({identifier}) on PubChem. Status: {response.status_code}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    print("Starting PubChem MOL file fetch sequence...\n")
    
    for filename, identifier in molecules.items():
        fetch_mol_file(identifier, filename)
        # PubChem requires rate limiting (max 5 requests per second)
        # Sleeping for 300ms ensures we stay well within API limits
        time.sleep(0.3)
        
    print("\nFinished fetching MOL files.")

if __name__ == "__main__":
    main()
