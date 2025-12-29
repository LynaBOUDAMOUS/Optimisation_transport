# ihm_logic.py

"""Module de logique métier pour l'application d'optimisation de transport.
Ce module encapsule la logique métier de l'application, gère les fichiers de données,
et orchestre l'algorithme d'optimisation."""

import pandas as pd # Importe la bibliothèque pandas pour la manipulation de données tabulaires (DataFrames)
import csv          # Importe le module csv pour la lecture et l'écriture de fichiers CSV
import os           # Importe le module os pour interagir avec le système d'exploitation (vérifier l'existence de fichiers, etc.)
import shutil       # Importe le module shutil pour les opérations sur les fichiers (copie de fichiers)
import re           # Importe le module re pour les expressions régulières (utilisé par extraire_chiffre)

# Importe la fonction d'optimisation. Cette fonction est considérée comme une dépendance externe
# pour la logique de l'IHM, mais son code n'est pas inclus ici.
from optimisation import run_optimization

# --- Constantes pour les noms de fichiers (définies une seule fois ici pour toute la logique) ---
DATA_FILE = "transport.csv"
TEMP_FILE = "transport_temp.csv"
DELAIS_FILE = "delais_livraison.csv"

# --- Fonctions utilitaires génériques (peuvent être déplacées dans un module 'utils.py' si elles sont utilisées ailleurs) ---
def extraire_chiffre(cellule):
    """
    Extrait le premier nombre entier trouvé dans une chaîne de caractères.

    Cette fonction est utile pour nettoyer des chaînes comme "Client 5" ou "10T"
    afin d'en récupérer la valeur numérique pure.

    Args:
        cellule (str ou int ou autre type): La valeur à partir de laquelle extraire un chiffre.
                                            Sera convertie en chaîne avant la recherche.

    Returns:
        int: Le premier nombre entier trouvé dans la chaîne. Retourne 0 si aucun nombre n'est trouvé
             ou si la conversion échoue.
    """
    # Convertit la cellule en chaîne de caractères pour s'assurer que re.search fonctionne
    match = re.search(r'\d+', str(cellule))
    # Si un nombre est trouvé, le convertit en entier et le retourne, sinon retourne 0
    return int(match.group()) if match else 0

def lire_transport_csv(filepath):
    """
    Lit un fichier CSV de données de transport.

    Cette fonction lit le fichier spécifié, en s'assurant que chaque ligne
    a au moins 6 éléments en ajoutant des chaînes vides si nécessaire.
    Elle retourne les données brutes telles que lues, sans conversion de type
    numérique, car cette conversion est gérée à un stade ultérieur par la logique
    d'optimisation ou de traitement des résultats.

    Args:
        filepath (str): Le chemin vers le fichier CSV.

    Returns:
        list: Une liste de listes représentant les données lues. Chaque élément
              est une chaîne de caractères brute. Retourne une liste vide si
              le fichier n'est pas trouvé.
    """
    data = []
    try:
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';') # Le délimiteur est le point-virgule
            for row in reader:
                if not row: # Ignorer les lignes complètement vides
                    continue
                # Assure que la ligne a au moins 6 éléments en ajoutant des chaînes vides.
                # Ceci évite les erreurs d'index lors de l'accès aux colonnes.
                while len(row) < 6:
                    row.append('')
                data.append(row)
    except FileNotFoundError:
        # Affiche un avertissement si le fichier n'existe pas, mais ne lève pas d'erreur
        # pour permettre à l'application de continuer avec des données vides.
        print(f"Avertissement : Le fichier '{filepath}' n'a pas été trouvé. Retourne des données vides.")
        return []
    return data

def sauver_csv(filepath, data):
    """
    Sauvegarde une liste de listes (données brutes) dans un fichier CSV.

    Args:
        filepath (str): Le chemin où sauvegarder le fichier CSV.
        data (list): La liste de listes de chaînes à écrire dans le CSV.
    """
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';') # Utilise le point-virgule comme délimiteur
            writer.writerows(data)
    except IOError as e:
        # Affiche une erreur si la sauvegarde échoue (permissions, disque plein, etc.)
        print(f"Erreur lors de la sauvegarde du fichier '{filepath}' : {e}")
        # En production, on pourrait propager l'exception ou la gérer plus spécifiquement.

# --- Classe de Logique Métier Principale de l'Application ---
class MainAppLogic:
    """
    Encapsule la logique métier principale de l'application d'optimisation du transport.

    Cette classe est responsable de la gestion des fichiers de données, de l'orchestration
    de l'algorithme d'optimisation, et de la préparation des résultats sous une forme
    facilement utilisable par l'interface utilisateur. Elle est conçue pour être
    indépendante de toute bibliothèque d'interface graphique (comme Tkinter).
    """
    def __init__(self, data_file=DATA_FILE, temp_file=TEMP_FILE, delais_file=DELAIS_FILE):
        """
        Initialise l'objet MainAppLogic avec les chemins vers les fichiers de données.

        Args:
            data_file (str): Chemin vers le fichier CSV de données original (source).
            temp_file (str): Chemin vers le fichier CSV temporaire de travail.
            delais_file (str): Chemin vers le fichier CSV contenant les données de délais de livraison.
        """
        self.data_file = data_file
        self.temp_file = temp_file
        self.delais_file = delais_file

    def reset_data_to_original(self):
        """
        Réinitialise le fichier de données temporaire (`TEMP_FILE`) à partir
        du fichier de données original (`DATA_FILE`).

        Cette opération permet de revenir à un état initial des données de travail.

        Returns:
            bool: True si la réinitialisation a réussi, False sinon (par exemple,
                  si le fichier source n'existe pas).
        """
        if os.path.exists(self.data_file):
            try:
                shutil.copy(self.data_file, self.temp_file)
                return True
            except IOError as e:
                print(f"Erreur lors de la copie de '{self.data_file}' vers '{self.temp_file}' : {e}")
                return False
        else:
            print(f"Erreur: Fichier source original '{self.data_file}' introuvable pour la réinitialisation.")
            return False

    def prepare_and_run_optimization(self, with_delays: bool):
        """
        Prépare les données pour l'optimisation, exécute l'algorithme d'optimisation,
        et traite les résultats pour l'affichage.

        Cette méthode est le cœur de la logique métier, elle orchestre les étapes clés.

        Args:
            with_delays (bool): Indique si l'algorithme d'optimisation doit prendre
                                 en compte les contraintes de délais de livraison.

        Returns:
            tuple: Un tuple contenant quatre éléments :
                   - total_cost (float): Le coût total calculé de l'optimisation.
                   - remaining_quantities (list): Une liste de tuples (entrepôt, quantité_restante)
                                                  pour les entrepôts.
                   - unsatisfied_clients (list): Une liste de tuples (client, quantité_non_satisfaite)
                                                pour les clients non entièrement servis.
                   - treeview_data (list): Une liste de dictionnaires structurée, prête à être
                                           insérée dans un widget Treeview de l'IHM. Chaque dictionnaire
                                           représente un client et ses livraisons.

        Raises:
            Exception: Propagera toute exception levée par `run_optimization`
                       ou lors de la lecture des fichiers, permettant à l'IHM
                       de gérer et d'afficher l'erreur.
        """
        # 1. Vérifier et préparer le fichier temporaire de travail
        if not os.path.exists(self.temp_file):
            if not self.reset_data_to_original():
                # Si le fichier temp n'existe pas et la copie depuis l'original échoue
                raise FileNotFoundError(f"Impossible de trouver ou de créer '{self.temp_file}'.")

        # Sauvegarder les données actuelles dans TEMP_FILE avant l'optimisation.
        # Cela garantit que `run_optimization` travaille toujours sur la version la plus à jour.
        data_for_optimization = lire_transport_csv(self.temp_file)
        sauver_csv(self.temp_file, data_for_optimization)

        # 2. Exécuter l'algorithme d'optimisation
        # La fonction `run_optimization` (importée de OptiFIN_3) est supposée
        # lire `TEMP_FILE` et `DELAIS_FILE` en interne.
        results_raw, remaining_quantities, unsatisfied_clients = run_optimization(with_delays=with_delays)

        total_cost = 0.0
        treeview_data = [] # Structure pour l'affichage hiérarchique dans le Treeview

        # 3. Charger les données de délais si l'option est activée
        delais_df = None
        ligne_max_delais = pd.Series(dtype=object) # Utilise 'object' pour gérer 'int' ou ''
        if with_delays:
            try:
                # pandas lit le CSV des délais, la première colonne est l'index.
                delais_df = pd.read_csv(self.delais_file, index_col=0, sep=',', dtype=str)
                # Extraire la ligne des délais max des clients si elle existe dans l'index
                if "Max_Delai_Client" in delais_df.index:
                    ligne_max_delais = delais_df.loc["Max_Delai_Client"]
                    delais_df = delais_df.drop("Max_Delai_Client") # La supprimer du DataFrame principal
                else:
                    # Si la ligne 'Max_Delai_Client' n'existe pas, assurez-vous que ligne_max_delais est vide.
                    ligne_max_delais = pd.Series(dtype=object)
            except FileNotFoundError:
                print(f"Avertissement: Fichier de délais '{self.delais_file}' introuvable. Les délais ne seront pas affichés.")
                delais_df = None # Mettre à None si le fichier manque pour ne pas tenter de l'utiliser
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier de délais '{self.delais_file}': {e}")
                delais_df = None # En cas d'erreur de lecture, ignorer les délais

        # 4. Regrouper et formater les résultats pour le Treeview
        clients_dict = {}
        last_client_name = None # Pour gérer les lignes où le nom du client n'est pas répété dans results_raw

        # Itérer sur les résultats bruts de l'optimisation
        # Chaque élément de results_raw doit avoir exactement 6 valeurs
        # [nom_client (ou vide), nom_entrepot, quantité, coût_unitaire, prix, total_client_partiel]
        for client_entry, entrepot, qty, cout_unit, prix, total_client_item in results_raw:
            # Si client_entry n'est pas vide, c'est le début d'un nouveau client ou la première ligne de ses livraisons
            if client_entry and str(client_entry).strip():
                last_client_name = client_entry # Met à jour le nom du client courant

            # Utilise toujours le dernier nom de client valide pour grouper les livraisons
            current_client = last_client_name
            # Gérer le cas où current_client est None au début (ne devrait pas arriver si le premier élément de results_raw
            # a toujours un nom de client, mais c'est une garde-fou)
            if current_client is None:
                # Si pour une raison quelconque, le client ne peut pas être identifié, on ignore la ligne.
                # En production, on pourrait vouloir logguer une erreur ou lever une exception.
                continue 

            if current_client not in clients_dict:
                clients_dict[current_client] = []

            # Ajoute les détails de la livraison (de l'entrepôt au client)
            clients_dict[current_client].append({
                'entrepot': entrepot,
                'qty': qty,
                'cout_unit': cout_unit,
                'prix': prix,
                'total_client_item': total_client_item
            })

        # Construire la structure finale pour le Treeview
        for client, deliveries_data in clients_dict.items():
            client_total_cost = 0.0
            client_items_for_treeview = [] # Liste des lignes d'entrepôt pour ce client

            for delivery in deliveries_data:
                entrepot = delivery['entrepot']
                qty = delivery['qty']
                cout_unit = delivery['cout_unit']
                prix = delivery['prix']
                total_client_item = delivery['total_client_item']

                # Calcul du coût total pour ce client
                try:
                    # S'assure que la valeur est bien un flottant avant l'addition.
                    # Le try-except gère les cas où la valeur ne serait pas numérique.
                    client_total_cost += float(total_client_item)
                except ValueError:
                    # Ignore les valeurs non numériques dans total_client_item pour le calcul du coût.
                    pass

                delai_val = ""
                delai_max_val = ""

                # Seulement si l'option avec délais est activée ET que le DataFrame des délais a été chargé avec succès
                if with_delays and delais_df is not None:
                    try:
                        # Formate les clés pour correspondre aux index/colonnes du DataFrame des délais
                        # Ex: 'Client 1' pour un client nommé 'Client 1'
                        client_key_for_delays = f"Client {extraire_chiffre(client)}"
                        # Ex: 'Entrepot 1' pour un entrepôt nommé 'Entrepôt 1'
                        entrepot_key_for_delays = f"Entrepot {extraire_chiffre(entrepot)}"

                        # Récupère le délai de livraison spécifique entre l'entrepôt et le client
                        # .at[] est utilisé pour un accès rapide par label d'index et de colonne
                        delai_str = delais_df.at[entrepot_key_for_delays, client_key_for_delays]
                        delai_val = int(float(delai_str)) if delai_str else "" # Convertit en int si possible
                    except (KeyError, ValueError, TypeError):
                        # Si le délai n'existe pas ou le format est incorrect, laisse vide
                        delai_val = ""

                    try:
                        # Récupère le délai maximal autorisé pour ce client
                        dm_str = ligne_max_delais.get(client_key_for_delays, "")
                        delai_max_val = int(float(dm_str)) if dm_str else "" # Convertit en int si possible
                    except (KeyError, ValueError, TypeError):
                        delai_max_val = ""

                # Construit la liste des valeurs pour la ligne de l'entrepôt dans le Treeview
                item_values = [entrepot, qty, cout_unit, prix, total_client_item]
                # Ajoute les colonnes de délais uniquement si les délais sont activés ET disponibles
                if with_delays and delais_df is not None:
                    item_values += [delai_val, delai_max_val]
                client_items_for_treeview.append(item_values)

            # Ajoute les données du client (parent) avec ses livraisons (enfants)
            treeview_data.append({
                'client': client,
                'total_cost_client': client_total_cost,
                'items': client_items_for_treeview
            })
            total_cost += client_total_cost # Accumule le coût total global

        return total_cost, remaining_quantities, unsatisfied_clients, treeview_data