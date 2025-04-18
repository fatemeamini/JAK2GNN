import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import requests
import logging
import tkinter.font as tkFont

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Original BindingDB data fetching function
def download_binding_affinity(pdb_code, cutoff=10000):
    all_ligand_data = []
    url = f'https://bindingdb.org/axis2/services/BDBService/getLigandsByPDBs?pdb={pdb_code}&cutoff={cutoff}&identity=98&response=application/json'

    try:
        logging.info(f"Requesting binding affinity data for PDB code: {pdb_code}")
        response = requests.get(url)
        response.raise_for_status()

        json_data = response.json()
        if isinstance(json_data, dict) and 'getLigandsByPDBsResponse' in json_data:
            response_data = json_data['getLigandsByPDBsResponse']

            if isinstance(response_data, dict) and 'affinities' in response_data:
                actual_data = response_data['affinities']

                if isinstance(actual_data, list):
                    for ligand in actual_data:
                        ligand_info = {
                            'PDB ID': pdb_code,
                            'SMILES': ligand.get('smile', ''),
                            'Affinity Type': ligand.get('affinity_type', ''),
                            'Affinity': ligand.get('affinity', ''),
                            'PubMed ID': ligand.get('pmid', ''),
                            'DOI': ligand.get('doi', ''),
                            'BindingDB URL': f"https://www.bindingdb.org/bind/chemsearch/marvin/MolStructure.jsp?monomerid={ligand.get('monomerid')}"
                        }
                        all_ligand_data.append(ligand_info)
                else:
                    logging.warning(f"No data available for PDB code: {pdb_code}.")
            else:
                logging.warning(f"'affinities' key not found for PDB code: {pdb_code}.")
        else:
            logging.warning(f"'getLigandsByPDBsResponse' key not found for PDB code: {pdb_code}.")

    except requests.HTTPError as http_err:
        logging.error(f"HTTP error occurred for PDB code {pdb_code}: {http_err}")
    except requests.RequestException as req_err:
        logging.error(f"Error downloading data for PDB code {pdb_code}: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred for PDB code {pdb_code}: {e}")

    return all_ligand_data

# Placeholder functions for additional databases (implement similar to BindingDB as needed)
def download_rcsb_data(pdb_code):
    # Placeholder for RCSB data fetching logic
    logging.info(f"Placeholder: Requesting RCSB data for PDB code: {pdb_code}")
    return []

def download_uniprot_data(pdb_code):
    # Placeholder for UniProt data fetching logic
    logging.info(f"Placeholder: Requesting UniProt data for PDB code: {pdb_code}")
    return []

def download_ncbi_data(pdb_code):
    # Placeholder for NCBI data fetching logic
    logging.info(f"Placeholder: Requesting NCBI data for PDB code: {pdb_code}")
    return []

def download_zinc_data(pdb_code):
    # Placeholder for ZINC data fetching logic
    logging.info(f"Placeholder: Requesting ZINC data for PDB code: {pdb_code}")
    return []

def collect_data(protein, db_selections):
    all_data = []
    pdb_codes = {
        "JAK1": ["4E4V", "5TUT"],
        "JAK2": ["3KRR", "6VAP"],
        "JAK3": ["3ZC6", "5TOZ"],
        "TYK2": ["4GIH", "6NPA"],
        # "Serotonin": ["7XT8"],
        # "Acetylcholine Esterase": ["4M0E"],
        # "Serotonin Receptor": ["7E2Y"],
        # "Dopamine RECEPTOR D1": ["7CMV"],
    }
    
    api_functions = {
        "BindingDB": download_binding_affinity,
        "RCSB": download_rcsb_data,
        "UniProt": download_uniprot_data,
        "NCBI": download_ncbi_data,
        "ZINC": download_zinc_data,
    }
    
    for pdb_code in pdb_codes.get(protein, []):
        protein_data = {"protein": protein, "PDB ID": pdb_code}
        for database in db_selections:
            logging.info(f'Collecting data for protein {protein} from database {database}')
            try:
                results = api_functions[database](pdb_code)
                for result in results:
                    data_entry = protein_data.copy()
                    data_entry.update(result)
                    all_data.append(data_entry)
            except Exception as e:
                logging.error(f'Error collecting data from {database} for protein {protein}: {e}')
                messagebox.showerror("Data Collection Error", f"Failed to collect data from {database} for protein {protein}")

    return all_data

def download_data():
    db_selections = [db for db, var in db_vars.items() if var.get()]
    protein_selections = [protein for protein, var in protein_vars.items() if var.get()]
    
    logging.info(f'Selected databases: {db_selections}')
    logging.info(f'Selected proteins: {protein_selections}')

    if not protein_selections or not db_selections:
        messagebox.showerror("Error", "No proteins or databases selected.")
        return

    collected_data = []
    for protein in protein_selections:
        collected_data.extend(collect_data(protein, db_selections))

    if collected_data:
        df = pd.DataFrame(collected_data)
        excel_filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                      filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if excel_filename:
            df.to_excel(excel_filename, index=False)
            messagebox.showinfo("Success", f"Data saved to {excel_filename}")
    else:
        messagebox.showwarning("No Data", "No data was retrieved for the selected options.")

    root.destroy()

root = tk.Tk()
root.title("Protein Ligand Binding Affinity Downloader")

default_font = tkFont.nametofont("TkDefaultFont")
default_font.configure(size=12)
root.option_add("*TCombobox*Listbox*Font", default_font)

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Database selection with check buttons
ttk.Label(frame, text="Select Databases:").grid(row=0, column=0, pady=5, sticky=tk.W)
db_options = ["BindingDB", "RCSB", "UniProt", "NCBI", "ZINC"]
db_vars = {db: tk.BooleanVar() for db in db_options}

db_frame = ttk.Frame(frame)
db_frame.grid(row=0, column=1, pady=5, sticky=(tk.W, tk.E))

for db in db_options:
    check = ttk.Checkbutton(db_frame, text=db, variable=db_vars[db])
    check.pack(anchor=tk.W)

# Protein class selection
ttk.Label(frame, text="Select Protein Classes:").grid(row=1, column=0, pady=5, sticky=tk.W)
protein_options = [
    # "Serotonin", "Acetylcholine Esterase",
    # "Serotonin Receptor", "Dopamine RECEPTOR D1",
    "JAK1", "JAK2", "JAK3", "TYK2"
]
protein_vars = {protein: tk.BooleanVar() for protein in protein_options}

protein_frame = ttk.Frame(frame)
protein_frame.grid(row=1, column=1, pady=5, sticky=(tk.W, tk.E))

for protein in protein_options:
    check = ttk.Checkbutton(protein_frame, text=protein, variable=protein_vars[protein])
    check.pack(anchor=tk.W)

download_button = ttk.Button(frame, text="Download", command=download_data)
download_button.grid(row=2, columnspan=2, pady=10)

root.mainloop()
