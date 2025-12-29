# === Importation des modules nécessaires ===
import tkinter as tk  # Bibliothèque pour créer l'interface graphique
from tkinter import ttk, messagebox  # Widgets avancés + boîtes de message
import shutil  # Pour copier des fichiers
import os  # Pour les opérations sur le système de fichiers
import pandas as pd  # Pour manipuler les fichiers CSV des délais
import csv  # Pour lire/écrire les fichiers CSV
from optimisation import run_optimization  # Fonction d'optimisation (module externe)
from gerer_clients import open_gestion_clients  # Interface de gestion des clients
from gerer_entrepots import open_gestion_entrepots  # Interface de gestion des entrepôts
from gerer_delais import open_gestion_delais  # Interface de gestion des délais

# === Déclaration des chemins de fichiers utilisés ===
DATA_FILE = "transport.csv"  # Fichier source principal des données transport
TEMP_FILE = "transport_temp.csv"  # Fichier temporaire pour sauvegarder les modifications
DELAIS_FILE = "delais_livraison.csv"  # Fichier contenant les délais de livraison

# === Fonctions de lecture et écriture CSV ===

def lire_transport_csv(filepath):
    """
    Lit un fichier CSV délimité par ';' contenant les données de transport.
    Convertit les colonnes 3, 4 et 5 en flottants (quantité, coût unitaire, prix).
    Gère les lignes incomplètes et remplace les valeurs incorrectes par 0.0.
    """
    data = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if not row:
                continue
            while len(row) < 6:
                row.append('')
            for idx in [2, 3, 4]:  # Colonnes numériques à convertir
                try:
                    row[idx] = float(row[idx].replace(',', '.') if row[idx] else 0.0)
                except Exception:
                    row[idx] = 0.0
            data.append(row)
    return data

def sauver_csv(filepath, data):
    """
    Sauvegarde les données fournies dans un fichier CSV délimité par ';'.
    """
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(data)

# === Interface principale (fenêtre tkinter) ===
root = tk.Tk()
root.title("Optimisation du transport")  # Titre de la fenêtre principale

# === Frame contenant les boutons de gestion ===
frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

# Ouverture des interfaces de gestion associées

def manage_entrepots():
    """
    Ouvre la fenêtre de gestion des entrepôts.
    """
    open_gestion_entrepots(root)

def manage_clients():
    """
    Ouvre la fenêtre de gestion des clients.
    """
    open_gestion_clients(root)

def manage_delais():
    """
    Ouvre la fenêtre de gestion des délais avec rappel pour mise à jour.
    """
    open_gestion_delais(root, callback=update_table)

def reinitialiser_donnees():
    """
    Réinitialise les données en copiant le fichier source dans le fichier temporaire,
    puis met à jour la table et affiche un message de confirmation.
    """
    shutil.copy(DATA_FILE, TEMP_FILE)
    update_table()
    messagebox.showinfo("Réinitialisation", "Les données ont été réinitialisées.")

# Création des boutons principaux pour la gestion
tk.Button(frame_buttons, text="Gérer entrepôts", command=manage_entrepots).grid(row=0, column=0, padx=5)
tk.Button(frame_buttons, text="Gérer clients", command=manage_clients).grid(row=0, column=1, padx=5)
tk.Button(frame_buttons, text="Actualiser", command=lambda: update_table()).grid(row=0, column=2, padx=5)
tk.Button(frame_buttons, text="Réinitialiser", command=reinitialiser_donnees).grid(row=0, column=3, padx=5)

# === Section pour la gestion des délais ===
frame_delais = tk.Frame(root)
frame_delais.pack(pady=(0, 10))

delais_var = tk.BooleanVar()  # Variable d'état pour la checkbox de prise en compte des délais

# Checkbox permettant d'activer/désactiver la prise en compte des délais
chk_delais = tk.Checkbutton(
    frame_delais,
    text="Prendre en compte les délais",
    variable=delais_var,
    command=lambda: (toggle_delais_button(), update_table())
)
chk_delais.pack(side=tk.LEFT)

# Bouton pour gérer les délais, affiché uniquement si la checkbox est activée
bouton_delais = tk.Button(frame_delais, text="Gérer les délais", command=manage_delais)

def toggle_delais_button():
    """
    Affiche ou masque le bouton 'Gérer les délais' selon l'état de la checkbox.
    """
    if delais_var.get():
        bouton_delais.pack(side=tk.LEFT, padx=5)
    else:
        bouton_delais.pack_forget()

# === Table de résultats (Treeview) ===
tree_frame = tk.Frame(root)
tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)

tree = None  # Variable globale pour le tableau des résultats

# Colonnes de base sans délais
cols_base = ["Entrepôt", "Quantité", "$/T", "Prix", "Total client"]
# Colonnes avec les délais de livraison ajoutées
cols_avec_delais = cols_base + ["Délai de livraison", "Délai max accepté"]

def create_treeview(with_delais):
    """
    Crée dynamiquement le tableau Treeview avec ou sans colonnes délais.
    Efface l'ancien tableau avant de recréer.
    """
    global tree
    for widget in tree_frame.winfo_children():
        widget.destroy()
    columns = cols_avec_delais if with_delais else cols_base
    tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
    tree.heading("#0", text="Client")  # Colonne principale affichant les clients
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=110, anchor=tk.CENTER)
    tree.pack(fill=tk.BOTH, expand=True)

# === Zone de bas de page pour les résumés ===
bottom_frame = tk.Frame(root)
bottom_frame.pack(pady=5)

total_label = tk.Label(bottom_frame, text="", fg="blue")  # Affiche le coût total
restants_label = tk.Label(bottom_frame, text="", fg="green")  # Quantités restantes non utilisées
non_satis_label = tk.Label(bottom_frame, text="", fg="red")  # Clients non satisfaits

total_label.pack(side=tk.LEFT, padx=10)
restants_label.pack(side=tk.LEFT)
non_satis_label.pack(side=tk.LEFT, padx=10)

# === Fonction centrale : mise à jour des données dans l'interface ===
def update_table():
    """
    Met à jour le tableau en fonction des données actuelles, exécute l'optimisation,
    affiche les résultats dans le tableau et met à jour les labels de résumé.
    """
    with_delais = delais_var.get()

    # Lecture des données source et sauvegarde dans le fichier temporaire
    data_lue = lire_transport_csv(TEMP_FILE if os.path.exists(TEMP_FILE) else DATA_FILE)
    sauver_csv(TEMP_FILE, data_lue)

    # Exécution de l'optimisation via le module externe
    try:
        results, restants, clients_non_satisfaits = run_optimization(with_delays=with_delais)
    except Exception as e:
        messagebox.showerror("Erreur", f"Problème d'optimisation : {e}")
        return

    create_treeview(with_delais)  # Recréation du tableau avec les bonnes colonnes

    # Lecture des délais si l'option est activée
    if with_delais:
        try:
            delais_df = pd.read_csv(DELAIS_FILE, index_col=0, sep=',', dtype=str)
            if "Max_Delai_Client" in delais_df.index:
                ligne_max = delais_df.loc["Max_Delai_Client"]
                delais_df = delais_df.drop("Max_Delai_Client")
            else:
                ligne_max = pd.Series(dtype=int)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lecture délais : {e}")
            return
    else:
        delais_df = None
        ligne_max = pd.Series(dtype=int)

    total_cost = 0  # Initialisation du coût total

    # Organisation des résultats par client
    clients_dict = {}
    last_client = None
    for raw_client, entrepot, qty, cout_unit, prix, total_client in results:
        if raw_client and str(raw_client).strip():
            last_client = raw_client
        client = last_client
        if client not in clients_dict:
            clients_dict[client] = []
        clients_dict[client].append((entrepot, qty, cout_unit, prix, total_client))

    # Remplissage du tableau avec les données par client
    for client, entrepots_data in clients_dict.items():
        parent_id = tree.insert("", tk.END, text=client, open=True, values=("", "", "", "", ""))
        client_total = 0
        for entrepot, qty, cout_unit, prix, total_client in entrepots_data:
            delai = ""
            delai_max = ""

            if with_delais and delais_df is not None:
                try:
                    client_key = f"Client {client.strip().split()[-1]}"
                    entrepot_key = f"Entrepot {entrepot.strip().split()[-1]}"
                    delai_str = delais_df.at[entrepot_key, client_key]
                    delai = int(float(delai_str))
                except Exception:
                    delai = ""
                try:
                    dm_str = ligne_max.get(client_key, "")
                    delai_max = int(float(dm_str)) if dm_str else ""
                except Exception:
                    delai_max = ""

            values = [entrepot, qty, cout_unit, prix, total_client]
            if with_delais:
                values += [delai, delai_max]

            tree.insert(parent_id, tk.END, text="", values=values)
            try:
                client_total += float(total_client)
            except:
                pass

        total_cost += client_total

    # Mise à jour des labels de résumé avec les résultats calculés
    total_label.config(text=f"Coût total : {total_cost:.2f} €")
    restants_label.config(
        text="Restants -> " + ", ".join(f"{e} : {q}T" for e, q in restants)
        if restants else ""
    )
    non_satis_label.config(
        text="Clients non satisfaits -> " + ", ".join(f"{c} : {q}T" for c, q in clients_non_satisfaits)
        if clients_non_satisfaits else ""
    )

# === Lancement initial de l'application ===
toggle_delais_button()  # Affiche/masque le bouton gérer délais au démarrage
update_table()  # Charge et affiche les données initiales

root.mainloop()  # Démarre la boucle principale de l'interface Tkinter
