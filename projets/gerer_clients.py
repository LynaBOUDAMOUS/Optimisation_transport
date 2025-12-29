# Importation de la bibliothèque tkinter pour l'interface graphique
import tkinter as tk  # Importation de modules spécifiques de tkinter
from tkinter import ttk, messagebox  # Importation de pandas pour la manipulation de données tabulaires
import pandas as pd
import re  # Importation du module re pour les expressions régulières
import random  # Importation du module random pour générer des valeurs aléatoires

# Nom du fichier CSV temporaire utilisé
TEMP_FILE = "transport_temp.csv"

def extraire_chiffre(cellule):
    """
    Extrait le premier chiffre trouvé dans une cellule (sous forme de chaîne) à l'aide d'expressions régulières.
    
    Args:
        cellule (str): La cellule à analyser.
    
    Returns:
        int: Le premier chiffre trouvé, ou 0 si aucun chiffre n'est présent.
    """
    match = re.search(r'\d+', str(cellule))  # Recherche du premier groupe de chiffres
    return int(match.group()) if match else 0  # Retourne le chiffre trouvé ou 0

def open_gestion_clients(parent_window=None):
    """
    Ouvre une nouvelle fenêtre tkinter pour gérer les clients :
    visualiser et modifier les demandes, masquer des clients,
    ou en ajouter de nouveaux avec leurs coûts et délais.
    
    Args:
        parent_window (tk.Tk or tk.Toplevel, optional): La fenêtre parente (si applicable).
    """
    df = pd.read_csv(TEMP_FILE, header=None)
    clients = df.iloc[0, 1:].tolist()

    window = tk.Toplevel(parent_window)
    window.title("Gestion des clients")

    selected_client_index = tk.IntVar(value=0)
    demande_var = tk.StringVar()

    def on_client_selected(event=None):
        """
        Met à jour le champ de quantité demandée en fonction du client sélectionné.
        """
        index = selected_client_index.get()
        valeur = df.iloc[0, index + 1]
        chiffre = extraire_chiffre(valeur)
        demande_var.set(str(chiffre))

    def appliquer_modification():
        """
        Applique une modification de la quantité demandée pour le client sélectionné
        et enregistre les modifications dans le fichier CSV.
        """
        try:
            nouvelle_valeur = int(demande_var.get())
            index = selected_client_index.get()
            nom_actuel = str(df.iloc[0, index + 1])
            if nom_actuel.startswith("#"):
                df.iloc[0, index + 1] = f"#{nouvelle_valeur}T"
            else:
                df.iloc[0, index + 1] = f"{nouvelle_valeur}T"
            df.to_csv(TEMP_FILE, index=False, header=False)
            messagebox.showinfo("Succès", "Demande modifiée avec succès.")
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre entier valide.")

    def masquer_clients_selectionnes():
        """
        Masque les clients sélectionnés dans la listbox (ajoute un # devant leur nom).
        Enregistre les modifications dans le fichier CSV.
        """
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Aucun client", "Veuillez sélectionner au moins un client à masquer.")
            return

        confirm = messagebox.askyesno("Confirmation", "Voulez-vous masquer le(s) client(s) sélectionné(s) ?")
        if not confirm:
            return

        for idx in selection:
            col_index = idx + 1
            original_value = str(df.iloc[0, col_index])
            if not original_value.startswith("#"):
                df.iloc[0, col_index] = f"#{original_value}"

        df.to_csv(TEMP_FILE, index=False, header=False)
        messagebox.showinfo("Masquage", "Client(s) masqué(s) avec succès.")
        window.destroy()

    def ajouter_client():
        """
        Ouvre une fenêtre pour ajouter un nouveau client avec son nom, quantité demandée,
        les coûts depuis chaque entrepôt, les délais, et le délai maximal accepté.
        """
        ajout_win = tk.Toplevel(window)
        ajout_win.title("Ajouter un client")

        nb_entrepots = len(df.iloc[1:, 0])

        nom_client_var = tk.StringVar()
        quantite_var = tk.StringVar()
        delai_var = tk.StringVar()
        couts_vars = []
        delais_vars = []

        main_frame = tk.Frame(ajout_win)
        main_frame.pack(padx=10, pady=10)

        left_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=10, sticky="n")

        tk.Label(left_frame, text="Nom du client :").grid(row=0, column=0, sticky="w")
        tk.Entry(left_frame, textvariable=nom_client_var).grid(row=0, column=1)

        tk.Label(left_frame, text="Quantité demandée (T) :").grid(row=1, column=0, sticky="w")
        tk.Entry(left_frame, textvariable=quantite_var).grid(row=1, column=1)

        tk.Label(left_frame, text="Coûts depuis chaque entrepôt :").grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        for i in range(nb_entrepots):
            var = tk.StringVar()
            couts_vars.append(var)
            tk.Label(left_frame, text=f"Entrepôt {i+1} :").grid(row=3 + i, column=0, sticky="w")
            tk.Entry(left_frame, textvariable=var).grid(row=3 + i, column=1)

        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=0, column=1, padx=10, sticky="n")

        info = tk.Label(right_frame, text="(Les délais ne sont pris en compte que si l'option est cochée dans le menu principale)", fg="gray")
        info.grid(row=0, column=1, columnspan=2, pady=(0, 0))

        tk.Label(right_frame, text="Délai max accepté (en jours) :").grid(row=1, column=0, sticky="w")
        tk.Entry(right_frame, textvariable=delai_var).grid(row=1, column=1)

        tk.Label(right_frame, text="Délai de livraison proposé par entrepôt :").grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        for i in range(nb_entrepots):
            var = tk.StringVar()
            delais_vars.append(var)
            tk.Label(right_frame, text=f"Entrepôt {i+1} :").grid(row=3 + i, column=0, sticky="w")
            tk.Entry(right_frame, textvariable=var).grid(row=3 + i, column=1)

        def simuler_couts():
            """
            Remplit automatiquement les champs de coût avec des valeurs aléatoires (1 à 5).
            """
            for var in couts_vars:
                var.set(str(random.randint(1, 5)))

        def simuler_delais():
            """
            Remplit automatiquement les champs de délai avec des valeurs aléatoires (1 à 5).
            """
            delai_var.set(str(random.randint(1, 5)))
            for var in delais_vars:
                var.set(str(random.randint(1, 5)))

        def valider_ajout():
            """
            Valide les données saisies et ajoute le client dans le fichier CSV ainsi que dans le fichier
            des délais de livraison.
            """
            try:
                quantite = int(quantite_var.get())
                couts = [int(v.get()) for v in couts_vars]
                delais = [int(v.get()) for v in delais_vars]
                delai_max = int(delai_var.get())

                print("1")

                if len(couts) != nb_entrepots or len(delais) != nb_entrepots:
                    raise ValueError("Nombre de coûts ou délais incorrect")

                print("2")

                nouveau_nom_client = f"Client {df.shape[1]}"
                nouvelle_colonne = [f"{quantite}T"] + [f"{c}€" for c in couts]

                df[nouveau_nom_client] = nouvelle_colonne
                df.to_csv(TEMP_FILE, index=False, header=False)

                print("3")

                try:
                    delais_df = pd.read_csv("delais_livraison.csv", index_col=0)
                except FileNotFoundError:
                    messagebox.showerror("Erreur", "Le fichier delais_livraison.csv est introuvable.")
                    return

                print("4")

                expected_rows = [f"Entrepot {i+1}" for i in range(nb_entrepots)] + ["Max_Delai_Client"]
                for row in expected_rows:
                    if row not in delais_df.index:
                        messagebox.showerror("Erreur", f"Ligne manquante dans delais_livraison.csv : {row}")
                        return

                print("5")

                delais_df[nouveau_nom_client] = pd.NA
                delais_df.at["Max_Delai_Client", nouveau_nom_client] = delai_max
                for i in range(nb_entrepots):
                    delais_df.at[f"Entrepot {i+1}", nouveau_nom_client] = delais[i]
                delais_df.to_csv("delais_livraison.csv")

                print("7")

                messagebox.showinfo("Succès", "Client ajouté avec succès.")
                ajout_win.destroy()
                window.destroy()

                print("8")

            except Exception as e:
                print("Erreur lors de l'ajout :", e)
                messagebox.showerror("Erreur", "Veuillez entrer des valeurs valides.")

        tk.Button(left_frame, text="Simuler les coûts", command=simuler_couts).grid(row=3 + nb_entrepots, column=0, columnspan=2, pady=(10,0))
        tk.Button(right_frame, text="Simuler les délais", command=simuler_delais).grid(row=4 + nb_entrepots, column=0, columnspan=2, pady=(10,0))
        tk.Button(ajout_win, text="Ajouter", command=valider_ajout).pack(pady=(0,10))

    frame = tk.Frame(window)
    frame.pack(padx=10, pady=10)

    tk.Label(frame, text="Sélectionnez un client :").grid(row=0, column=0, sticky="w")
    combo = ttk.Combobox(frame, values=[f"Client {i+1}" for i in range(len(clients))], state="readonly")
    combo.current(0)
    combo.grid(row=1, column=0, padx=5)
    combo.bind("<<ComboboxSelected>>", lambda e: selected_client_index.set(combo.current()) or on_client_selected())

    right_frame = tk.Frame(frame, bd=2, relief="groove", padx=10, pady=10)
    right_frame.grid(row=1, column=1, padx=10)

    tk.Label(right_frame, text="Quantité demandée (en T) :").pack(anchor="w")
    demande_row = tk.Frame(right_frame)
    demande_row.pack(fill="x", pady=2)
    tk.Entry(demande_row, textvariable=demande_var, width=10).pack(side="left")
    tk.Button(demande_row, text="Appliquer", command=appliquer_modification).pack(side="left", padx=10)

    frame_supp = tk.LabelFrame(window, text="Masquer des clients", padx=10, pady=5)
    frame_supp.pack(fill="both", padx=10, pady=10)

    listbox = tk.Listbox(frame_supp, selectmode="multiple", height=6)
    for i, name in enumerate(clients):
        prefix = "(masqué) " if str(name).startswith("#") else ""
        listbox.insert(tk.END, f"{prefix}Client {i+1}")
    listbox.pack(padx=5, pady=5)

    tk.Button(frame_supp, text="Masquer client(s)", command=masquer_clients_selectionnes).pack(pady=5)
    tk.Button(window, text="Ajouter un nouveau client", command=ajouter_client).pack(pady=5)

    on_client_selected()
