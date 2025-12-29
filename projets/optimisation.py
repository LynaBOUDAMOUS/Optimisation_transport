import pandas as pd
import numpy as np
import re
from scipy.optimize import linprog

# Fichier temporaire contenant les données de transport (quantités, coûts, etc.)
TEMP_FILE = "transport_temp.csv"

# --- Fonction utilitaire ---

def extraire_chiffre(cellule):
    """
    Extrait le premier chiffre entier trouvé dans une cellule.
    Si aucun chiffre n'est trouvé, retourne 0.
    
    Paramètre :
        cellule (str | int) : valeur de cellule (texte ou nombre)
    
    Retour :
        int : premier entier trouvé ou 0
    """
    match = re.search(r'\d+', str(cellule))
    return int(match.group()) if match else 0

# --- Fonction principale d'optimisation ---

def run_optimization(with_delays=False):
    """
    Effectue l'optimisation de transport entre entrepôts et clients,
    avec possibilité de prise en compte des délais de livraison.

    Paramètre :
        with_delays (bool) : indique si les délais de livraison doivent être
                             pris en compte comme pénalité dans les coûts

    Retour :
        rows (list) : liste des résultats formatés pour l'affichage (client, entrepôt, quantité, coût, prix, total)
        restants (list) : liste des quantités non livrées pour chaque entrepôt (si demande insuffisante)
        clients_non_satisfaits (list) : clients non entièrement satisfaits (si offre insuffisante)
    """
    # Chargement brut des données depuis le fichier CSV
    df = pd.read_csv(TEMP_FILE, header=None)

    # Extraction des masques (valeurs débutant par '#' sont ignorées)
    demandes_raw = df.iloc[0, 1:]
    clients_mask = [str(val).startswith("#") for val in demandes_raw]
    offres_raw = df.iloc[1:, 0]
    entrepots_mask = [str(val).startswith("#") for val in offres_raw]

    # Extraction des quantités visibles
    demandes = [extraire_chiffre(val) for val, mask in zip(demandes_raw, clients_mask) if not mask]
    offres = [extraire_chiffre(val) for val, mask in zip(offres_raw, entrepots_mask) if not mask]

    vis_clients_idx = [i for i, m in enumerate(clients_mask) if not m]
    vis_entrepots_idx = [i for i, m in enumerate(entrepots_mask) if not m]

    # Construction de la matrice des coûts
    couts_full = df.iloc[1:, 1:]
    couts = []
    for i in vis_entrepots_idx:
        row = []
        for j in vis_clients_idx:
            row.append(extraire_chiffre(couts_full.iat[i, j]))
        couts.append(row)
    couts = np.array(couts)

    # Ajout des pénalités de délai si demandé
    if with_delays:
        try:
            delais_df = pd.read_csv("delais_livraison.csv")
            for i, e_idx in enumerate(vis_entrepots_idx):
                for j, c_idx in enumerate(vis_clients_idx):
                    entrepot_nom = f"Entrepot {e_idx+1}"
                    client_nom = f"Client {c_idx+1}"
                    delai = delais_df.loc[delais_df["Entrepot"] == entrepot_nom, client_nom].values[0]
                    couts[i][j] += delai  # pénalité ajoutée au coût de transport
        except Exception as e:
            print("Erreur chargement délais :", e)

    # Gestion des cas d'inégalité entre offre et demande
    total_offre = sum(offres)
    total_demande = sum(demandes)

    client_fictif = False
    entrepot_fictif = False
    clients_non_satisfaits = []

    # Ajout d'un client fictif si trop d'offre
    if total_offre > total_demande:
        client_fictif = True
        manque = total_offre - total_demande
        demandes.append(manque)
        couts = np.hstack((couts, np.zeros((couts.shape[0], 1), dtype=int)))

    # Ajout d'un entrepôt fictif si trop de demande
    elif total_offre < total_demande:
        entrepot_fictif = True
        manque = total_demande - total_offre
        offres.append(manque)
        couts_fictif = np.full((1, len(demandes)), 10**6, dtype=int)  # pénalité élevée
        couts = np.vstack((couts, couts_fictif))

    # Définition du problème linéaire
    num_sources, num_dest = couts.shape
    c = couts.flatten()
    A_eq = []
    b_eq = []

    # Contraintes d'offre (chaque entrepôt ne peut livrer que sa capacité)
    for i, offre in enumerate(offres):
        row = [0] * (num_sources * num_dest)
        for j in range(num_dest):
            row[i * num_dest + j] = 1
        A_eq.append(row)
        b_eq.append(offre)

    # Contraintes de demande (chaque client doit recevoir sa demande)
    for j, demande in enumerate(demandes):
        row = [0] * (num_sources * num_dest)
        for i in range(num_sources):
            row[i * num_dest + j] = 1
        A_eq.append(row)
        b_eq.append(demande)

    # Résolution du problème d'optimisation
    res = linprog(c=c, A_eq=A_eq, b_eq=b_eq, method="highs")

    if not res.success:
        return [], [], []

    # Résultats arrondis et formatés
    x = np.round(res.x.reshape((num_sources, num_dest))).astype(int)

    entrepot_labels = [f"Entrepôt {i+1}" for i in vis_entrepots_idx]
    client_labels = [f"Client {i+1}" for i in vis_clients_idx]

    if entrepot_fictif:
        entrepot_labels.append("Entrepôt fictif")

    rows = []
    for j in range(len(client_labels)):
        total_client = sum(
            x[i, j] * couts[i, j] for i in range(num_sources) if (not entrepot_fictif or i != num_sources-1)
        )
        first = True
        for i in range(num_sources):
            qty = x[i, j]
            if qty > 0:
                if entrepot_fictif and i == num_sources - 1:
                    continue
                prix = qty * couts[i][j]
                rows.append([
                    client_labels[j] if first else "",
                    entrepot_labels[i],
                    qty,
                    couts[i][j],
                    prix,
                    total_client if first else ""
                ])
                first = False

    # Traitement des restes (offres inutilisées ou clients non servis)
    restants = []
    if client_fictif:
        for idx, r in enumerate(x[:, -1]):
            if r > 0:
                restants.append((entrepot_labels[idx], r))
    elif entrepot_fictif:
        for j in range(len(client_labels)):
            q = x[-1, j]
            if q > 0:
                clients_non_satisfaits.append((client_labels[j], q))

    return rows, restants, clients_non_satisfaits
