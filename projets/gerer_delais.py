import tkinter as tk                    # Module de base pour GUI
from tkinter import ttk, messagebox    # ttk : widgets modernes ; messagebox : boîtes de dialogue
import pandas as pd                    # Pour lire et modifier le CSV
import os                              # Pour vérifier l’existence du fichier

DELAIS_FILE = "delais_livraison.csv"   # Chemin vers le fichier des délais

def open_gestion_delais(root, callback=None):
    """
    Ouvre une fenêtre pour modifier les délais de livraison entre entrepôts et clients,
    ainsi que les délais maximum acceptés par client.

    Paramètres :
        root (tk.Tk) : fenêtre principale tkinter
        callback (function) : fonction optionnelle appelée après modification (rafraîchissement)
    """
    # Vérifie que le fichier de délais existe
    if not os.path.exists(DELAIS_FILE):
        messagebox.showerror("Erreur", f"Fichier {DELAIS_FILE} introuvable.")
        return

    # Charge les données dans un DataFrame
    delais_df = pd.read_csv(DELAIS_FILE)

    # Clients = colonnes (hors "Entrepot")
    clients = list(delais_df.columns[1:])
    # Entrepôts = lignes sauf la spéciale "Max_Delai_Client"
    entrepots = [e for e in delais_df["Entrepot"].tolist() if e != "Max_Delai_Client"]

    # Fenêtre secondaire
    window = tk.Toplevel(root)
    window.title("Gestion des délais de livraison")

    # Conteneur principal
    frame = tk.Frame(window)
    frame.pack(padx=10, pady=10)

    # Variables pour stocker les sélections utilisateur
    selected_entrepot = tk.StringVar()
    selected_client = tk.StringVar()
    selected_client_max = tk.StringVar()
    delay_var = tk.StringVar()
    delai_max_var = tk.StringVar()

    # --- SECTION : Modification délai entrepôt <-> client ---
    tk.Label(frame, text="Modification du délai de livraison :").grid(row=0, column=0, columnspan=7, sticky="w", pady=(0, 5))

    delai_frame = tk.LabelFrame(frame, bd=1, relief="groove", padx=5, pady=5)
    delai_frame.grid(row=1, column=0, columnspan=7, sticky="ew", pady=(0, 10))

    tk.Label(delai_frame, text="Entrepôt :").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entrepot_menu = ttk.Combobox(delai_frame, textvariable=selected_entrepot, values=entrepots, state="readonly", width=15)
    entrepot_menu.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(delai_frame, text="Client :").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    client_menu = ttk.Combobox(delai_frame, textvariable=selected_client, values=clients, state="readonly", width=15)
    client_menu.grid(row=0, column=3, padx=5, pady=5)

    tk.Label(delai_frame, text="Délai (jours) :").grid(row=0, column=4, padx=5, pady=5, sticky="e")
    delay_entry = tk.Entry(delai_frame, textvariable=delay_var, width=7)
    delay_entry.grid(row=0, column=5, padx=5, pady=5)

    appliquer_btn = tk.Button(delai_frame, text="Appliquer")
    appliquer_btn.grid(row=0, column=6, padx=10, pady=5)

    # --- SECTION : Délai max accepté par client ---
    delai_max_frame = tk.LabelFrame(frame, text="Délai de livraison maximum accepté par le client", padx=10, pady=10)
    delai_max_frame.grid(row=2, column=0, columnspan=7, pady=(0, 10), sticky="ew")

    tk.Label(delai_max_frame, text="Client :").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    client_max_menu = ttk.Combobox(delai_max_frame, textvariable=selected_client_max, values=clients, state="readonly", width=15)
    client_max_menu.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(delai_max_frame, text="Délai max (jours) :").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    delai_max_entry = tk.Entry(delai_max_frame, textvariable=delai_max_var, width=10)
    delai_max_entry.grid(row=0, column=3, padx=5, pady=5)

    modifier_delai_max_btn = tk.Button(delai_max_frame, text="Modifier")
    modifier_delai_max_btn.grid(row=0, column=4, padx=10, pady=5)

    # --- Logique : Affichage automatique des valeurs dans les champs ---

    def afficher_delai(*args):
        """Affiche le délai actuel pour l'entrepôt/client sélectionné"""
        entrepot = selected_entrepot.get()
        client = selected_client.get()
        if entrepot in entrepots and client in clients:
            val = delais_df.loc[delais_df["Entrepot"] == entrepot, client].values[0]
            delay_var.set(str(val))

    def afficher_delai_max_client(*args):
        """Affiche le délai max actuel pour le client sélectionné"""
        client = selected_client_max.get()
        if "Max_Delai_Client" in delais_df["Entrepot"].values and client in clients:
            val_max = delais_df.loc[delais_df["Entrepot"] == "Max_Delai_Client", client].values[0]
            delai_max_var.set(str(val_max))
        else:
            delai_max_var.set("")

    # Déclenche l'affichage lors d’un changement de sélection
    selected_entrepot.trace_add('write', afficher_delai)
    selected_client.trace_add('write', afficher_delai)
    selected_client_max.trace_add('write', afficher_delai_max_client)


    def appliquer_modification():
        """Appliquer la modification d’un délai entrepôt-client"""
        entrepot = selected_entrepot.get()
        client = selected_client.get()
        try:
            val = int(delay_var.get())
            if val < 0:
                raise ValueError("Le délai doit être positif.")
            if entrepot not in entrepots or client not in clients:
                messagebox.showwarning("Attention", "Sélection invalide.")
                return
            # Modification dans DataFrame et sauvegarde
            delais_df.loc[delais_df["Entrepot"] == entrepot, client] = val
            delais_df.to_csv(DELAIS_FILE, index=False)
            messagebox.showinfo("Succès", f"Délai modifié pour {entrepot} - {client} : {val} jours")
        except ValueError as e:
            messagebox.showerror("Erreur", f"Valeur invalide : {e}")


    def modifier_delai_max():
        """Modifier le délai max pour un client"""
        client = selected_client_max.get()
        try:
            val = int(delai_max_var.get())
            if val < 0:
                raise ValueError("Le délai doit être positif.")
            if "Max_Delai_Client" not in delais_df["Entrepot"].values or client not in clients:
                messagebox.showwarning("Client invalide", "Aucun client sélectionné ou ligne Max_Delai_Client absente.")
                return
            # Mise à jour et sauvegarde
            delais_df.loc[delais_df["Entrepot"] == "Max_Delai_Client", client] = val
            delais_df.to_csv(DELAIS_FILE, index=False)
            messagebox.showinfo("Succès", f"Délai max modifié pour {client} : {val} jours")
            if callback:
                callback()  # Appelle le callback pour mettre à jour les affichages
        except ValueError as e:
            messagebox.showerror("Erreur", f"Valeur invalide : {e}")

    # Lien entre boutons et fonctions
    appliquer_btn.config(command=appliquer_modification)
    modifier_delai_max_btn.config(command=modifier_delai_max)

    # --- Bouton de fermeture avec sauvegarde ---
    def sauvegarder():
        """Sauvegarde les délais et ferme la fenêtre"""
        try:
            delais_df.to_csv(DELAIS_FILE, index=False)
            messagebox.showinfo("Succès", "Les délais ont été enregistrés dans le fichier.")
            window.destroy()
            if callback:
                callback()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d’enregistrer : {e}")

    save_btn = tk.Button(window, text="Fermer", command=sauvegarder)
    save_btn.pack(pady=(0, 10))

    # Initialisation des sélections par défaut
    if entrepots:
        selected_entrepot.set(entrepots[0])
    if clients:
        selected_client.set(clients[0])
        selected_client_max.set(clients[0])
        afficher_delai_max_client()
