# --- Importation des bibliothèques nécessaires pour l'interface graphique, la gestion des données, les expressions régulières et les tirages aléatoires ---
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import re
import random

# --- Fichier CSV temporaire contenant les données d'entrepôts ---
TEMP_FILE = "transport_temp.csv"

def extraire_chiffre(cellule):
    """
    Extrait le premier chiffre entier trouvé dans une cellule de texte.
    Exemple : "23T" → 23. Retourne 0 si aucun chiffre n'est trouvé.
    """
    match = re.search(r'\d+', str(cellule))
    return int(match.group()) if match else 0

def open_gestion_entrepots(parent_window=None):
    """
    Ouvre la fenêtre principale de gestion des entrepôts.
    Permet de consulter, modifier, masquer ou ajouter des entrepôts via une interface graphique.
    """

    df = pd.read_csv(TEMP_FILE, header=None)
    entrepots = df.iloc[1:, 0].tolist()

    window = tk.Toplevel(parent_window)
    window.title("Gestion des entrepôts")

    selected_entrepot_index = tk.IntVar(value=0)
    stock_var = tk.StringVar()

    def on_entrepot_selected(event=None):
        """
        Met à jour la valeur affichée du stock en fonction de l'entrepôt sélectionné.
        """
        index = selected_entrepot_index.get()
        valeur = df.iloc[index + 1, 0]
        chiffre = extraire_chiffre(valeur)
        stock_var.set(str(chiffre))

    def appliquer_modification():
        """
        Applique une modification de stock à l'entrepôt sélectionné et sauvegarde dans le CSV.
        """
        try:
            nouvelle_valeur = int(stock_var.get())
            index = selected_entrepot_index.get()
            nom_actuel = str(df.iloc[index + 1, 0])
            if nom_actuel.startswith("#"):
                df.iloc[index + 1, 0] = f"#{nouvelle_valeur}T"
            else:
                df.iloc[index + 1, 0] = f"{nouvelle_valeur}T"
            df.to_csv(TEMP_FILE, index=False, header=False)
            messagebox.showinfo("Succès", "Stock modifié avec succès.")
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre entier valide.")

    def masquer_entrepots_selectionnes():
        """
        Masque les entrepôts sélectionnés en les préfixant avec le symbole "#", puis sauvegarde.
        """
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Aucun entrepôt", "Veuillez sélectionner au moins un entrepôt à masquer.")
            return

        confirm = messagebox.askyesno("Confirmation", "Voulez-vous masquer le(s) entrepôt(s) sélectionné(s) ?")
        if not confirm:
            return

        for idx in selection:
            row_index = idx + 1
            original_value = str(df.iloc[row_index, 0])
            if not original_value.startswith("#"):
                df.iloc[row_index, 0] = f"#{original_value}"

        df.to_csv(TEMP_FILE, index=False, header=False)
        messagebox.showinfo("Masquage", "Entrepôt(s) masqué(s) avec succès.")
        window.destroy()

    def ajouter_entrepot():
        """
        Ouvre une fenêtre secondaire pour ajouter un nouvel entrepôt, incluant stock, coûts et délais.
        """

        ajout_win = tk.Toplevel(window)
        ajout_win.title("Ajouter un entrepôt")
        ajout_win.geometry("600x400")

        canvas = tk.Canvas(ajout_win)
        scrollbar = ttk.Scrollbar(ajout_win, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(scroll_frame, text="Stock disponible (T) :").grid(row=0, column=0, sticky="w")
        stock_var = tk.StringVar()
        tk.Entry(scroll_frame, textvariable=stock_var).grid(row=0, column=1)

        nb_clients = len(df.columns) - 1
        couts_vars = []
        delais_vars = []

        tk.Label(scroll_frame, text="Coûts vers chaque client (€)").grid(row=1, column=0, columnspan=2, sticky="w")

        phrase_grise = tk.Label(scroll_frame, text="Les délais ne sont pris en compte que si l'option est cochée dans le menu principale",
                                fg="gray")
        phrase_grise.grid(row=0, column=2, columnspan=2, sticky="w", pady=(0,5), padx=(25,0))

        tk.Label(scroll_frame, text="Délais vers chaque client (jours)").grid(row=1, column=2, columnspan=2, sticky="w", padx=(25,0))

        for i in range(nb_clients):
            cout_var = tk.StringVar()
            couts_vars.append(cout_var)
            tk.Label(scroll_frame, text=f"Client {i+1} :").grid(row=2 + i, column=0, sticky="w")
            tk.Entry(scroll_frame, textvariable=cout_var).grid(row=2 + i, column=1)

            delai_var = tk.StringVar()
            delais_vars.append(delai_var)
            tk.Label(scroll_frame, text=f"Client {i+1} :").grid(row=2 + i, column=2, sticky="w", padx=(25,0))
            tk.Entry(scroll_frame, textvariable=delai_var).grid(row=2 + i, column=2, sticky="n")

        def simuler_couts():
            """
            Simule des coûts aléatoires entre 1€ et 5€ pour tous les clients.
            """
            for var in couts_vars:
                var.set(str(random.randint(1, 5)))

        def simuler_delais():
            """
            Simule des délais aléatoires entre 1 et 5 jours pour tous les clients.
            """
            for var in delais_vars:
                var.set(str(random.randint(1, 5)))

        def valider_ajout():
            """
            Valide l'ajout d'un nouvel entrepôt avec stock, coûts, délais,
            et met à jour les fichiers CSV correspondants.
            """
            try:
                stock = int(stock_var.get())
                couts = [int(v.get()) for v in couts_vars]
                delais = [int(v.get()) for v in delais_vars]

                if len(couts) != nb_clients or len(delais) != nb_clients:
                    raise ValueError("Nombre de coûts ou de délais incorrect.")

                nouvelle_ligne = [f"{stock}T"] + [f"{c}€" for c in couts]
                df.loc[len(df)] = nouvelle_ligne
                df.to_csv(TEMP_FILE, index=False, header=False)

                try:
                    delais_df = pd.read_csv("delais_livraison.csv", index_col=0)
                except FileNotFoundError:
                    messagebox.showerror("Erreur", "Le fichier delais_livraison.csv est introuvable.")
                    return

                nom_entrepot = f"Entrepot {len(df) - 1}"
                if nom_entrepot in delais_df.index:
                    messagebox.showerror("Erreur", f"L'entrepôt {nom_entrepot} existe déjà dans les délais.")
                    return

                delais_df.loc[nom_entrepot] = [pd.NA] * delais_df.shape[1]
                for i in range(nb_clients):
                    client_col = delais_df.columns[i]
                    delais_df.at[nom_entrepot, client_col] = delais[i]

                delais_df.to_csv("delais_livraison.csv")

                messagebox.showinfo("Succès", "Entrepôt ajouté avec succès.")
                ajout_win.destroy()
                window.destroy()

            except Exception as e:
                print("Erreur :", e)
                messagebox.showerror("Erreur", "Veuillez entrer des valeurs valides.")

        final_row = 2 + nb_clients
        tk.Button(scroll_frame, text="Simuler coûts", command=simuler_couts).grid(row=final_row, column=0, pady=10)
        tk.Button(scroll_frame, text="Simuler délais", command=simuler_delais).grid(row=final_row, column=2, pady=10)
        tk.Button(scroll_frame, text="Ajouter", command=valider_ajout).grid(row=final_row + 1, column=0, columnspan=4, pady=10)

    frame = tk.Frame(window)
    frame.pack(padx=10, pady=10)

    tk.Label(frame, text="Sélectionnez un entrepôt :").grid(row=0, column=0, sticky="w")
    combo = ttk.Combobox(frame, values=[f"Entrepôt {i+1}" for i in range(len(entrepots))], state="readonly")
    combo.current(0)
    combo.grid(row=1, column=0, padx=5)
    combo.bind("<<ComboboxSelected>>", lambda e: selected_entrepot_index.set(combo.current()) or on_entrepot_selected())

    right_frame = tk.Frame(frame, bd=2, relief="groove", padx=10, pady=10)
    right_frame.grid(row=1, column=1, padx=10)

    tk.Label(right_frame, text="Stock disponible (en T) :").pack(anchor="w")

    stock_row = tk.Frame(right_frame)
    stock_row.pack(fill="x", pady=2)

    tk.Entry(stock_row, textvariable=stock_var, width=10).pack(side="left")
    tk.Button(stock_row, text="Appliquer", command=appliquer_modification).pack(side="left", padx=10)

    frame_supp = tk.LabelFrame(window, text="Masquer des entrepôts", padx=10, pady=5)
    frame_supp.pack(fill="both", padx=10, pady=10)

    listbox = tk.Listbox(frame_supp, selectmode="multiple", height=6)
    for i, name in enumerate(entrepots):
        prefix = "(masqué) " if str(name).startswith("#") else ""
        listbox.insert(tk.END, f"{prefix}Entrepôt {i+1}")
    listbox.pack(padx=5, pady=5)

    tk.Button(frame_supp, text="Masquer entrepôt(s)", command=masquer_entrepots_selectionnes).pack(pady=5)

    tk.Button(window, text="Ajouter un nouvel entrepôt", command=ajouter_entrepot).pack(pady=5)

    on_entrepot_selected()
