# client_manager_logic.py
""" CE MODULE GÈRE LA LOGIQUE MÉTIER DES CLIENTS ET LEURS DEMANDES
    Il est indépendant de l'interface utilisateur et gère les fichiers
    """
import pandas as pd
import re
import os

# Constantes pour les fichiers de données
TEMP_FILE = "transport_temp.csv"
DELAIS_FILE = "delais_livraison.csv"

def extraire_chiffre(cellule):
    """
    Extrait le premier nombre entier trouvé dans une chaîne de caractères.
    Retourne 0 si aucun nombre n'est trouvé.
    Ex: "10T" -> 10, "#50T" -> 50, "Client 1" -> 1, "abc" -> 0
    """
    match = re.search(r'\d+', str(cellule))
    return int(match.group()) if match else 0

class ClientManager:
    """
    Gère la logique métier liée aux clients, leurs demandes, et la gestion
    des fichiers `transport_temp.csv` et `delais_livraison.csv`.
    Cette classe est indépendante de l'interface utilisateur.
    """
    def __init__(self, temp_file=TEMP_FILE, delais_file=DELAIS_FILE):
        """
        Initialise le gestionnaire de clients en chargeant les données nécessaires.

        Args:
            temp_file (str): Chemin vers le fichier temporaire des transports (transport_temp.csv).
            delais_file (str): Chemin vers le fichier des délais de livraison (delais_livraison.csv).

        Raises:
            FileNotFoundError: Si l'un des fichiers de données spécifiés n'existe pas.
            Exception: Pour d'autres erreurs lors de la lecture des fichiers.
        """
        self.temp_file = temp_file
        self.delais_file = delais_file
        self.df_transport = self._load_transport_data()
        self.df_delais = self._load_delais_data() # Charge les délais pour l'ajout de client

    def _load_transport_data(self):
        """
        Charge les données depuis le fichier `transport_temp.csv`.

        Returns:
            pandas.DataFrame: Le DataFrame contenant les données de transport.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            Exception: Pour d'autres erreurs de lecture.
        """
        if not os.path.exists(self.temp_file):
            raise FileNotFoundError(f"Le fichier de données '{self.temp_file}' est introuvable.")
        try:
            # `header=None` car la première ligne contient les noms de clients et les stocks sont dans les colonnes
            return pd.read_csv(self.temp_file, header=None)
        except Exception as e:
            raise Exception(f"Erreur lors de la lecture du fichier de transport '{self.temp_file}': {e}")

    def _load_delais_data(self):
        """
        Charge les données depuis le fichier `delais_livraison.csv`.

        Returns:
            pandas.DataFrame: Le DataFrame contenant les données des délais.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            Exception: Pour d'autres erreurs de lecture.
        """
        if not os.path.exists(self.delais_file):
            raise FileNotFoundError(f"Le fichier des délais '{self.delais_file}' est introuvable.")
        try:
            # `index_col=0` car la première colonne est l'index (Entrepot, Max_Delai_Client)
            return pd.read_csv(self.delais_file, index_col=0, sep=',')
        except Exception as e:
            raise Exception(f"Erreur lors de la lecture du fichier des délais '{self.delais_file}': {e}")

    def _save_transport_data(self):
        """Sauvegarde le DataFrame `df_transport` dans `transport_temp.csv`."""
        try:
            self.df_transport.to_csv(self.temp_file, index=False, header=False)
        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde du fichier de transport '{self.temp_file}': {e}")

    def _save_delais_data(self):
        """Sauvegarde le DataFrame `df_delais` dans `delais_livraison.csv`."""
        try:
            self.df_delais.to_csv(self.delais_file, index=True) # index=True car index_col=0 à la lecture
        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde du fichier des délais '{self.delais_file}': {e}")

    def get_client_display_names(self):
        """
        Retourne une liste des noms de clients tels qu'ils devraient être affichés,
        en incluant le préfixe "(masqué)" si nécessaire.
        """
        clients = self.df_transport.iloc[0, 1:].tolist()
        display_names = []
        for i, name in enumerate(clients):
            prefix = "(masqué) " if str(name).startswith("#") else ""
            # On veut afficher "Client X" même si la valeur est "10T" ou "#5T"
            # On utilise l'index pour générer le nom "Client X"
            display_names.append(f"{prefix}Client {i + 1}")
        return display_names

    def get_client_actual_names(self):
        """
        Retourne la liste des noms des clients tels qu'ils sont dans la première ligne du CSV
        (e.g., 'Client 1', 'Client 2', ou '10T', '5T').
        """
        return self.df_transport.iloc[0, 1:].tolist()


    def get_client_demand(self, client_index):
        """
        Récupère la demande (quantité) d'un client spécifique.
        Args:
            client_index (int): L'index du client (0 pour le premier, etc.).
        Returns:
            int: La quantité demandée par le client.
        Raises:
            IndexError: Si l'index est hors limites.
        """
        if not (0 <= client_index < len(self.get_client_actual_names())):
            raise IndexError("Index de client hors limites.")
        
        # La demande est dans la première ligne du transport_temp.csv
        value = self.df_transport.iloc[0, client_index + 1] # +1 car la 1ère colonne est vide
        return extraire_chiffre(value)

    def update_client_demand(self, client_index, new_demand: int):
        """
        Met à jour la demande d'un client et sauvegarde le fichier.
        Args:
            client_index (int): L'index du client à modifier.
            new_demand (int): La nouvelle demande (quantité).
        Raises:
            ValueError: Si `new_demand` n'est pas un entier valide.
            IndexError: Si l'index du client est hors limites.
            Exception: Pour les erreurs de sauvegarde.
        """
        if not isinstance(new_demand, int) or new_demand < 0:
            raise ValueError("La demande doit être un nombre entier non négatif.")
        
        if not (0 <= client_index < len(self.get_client_actual_names())):
            raise IndexError("Index de client hors limites.")

        col_index = client_index + 1
        current_value = str(self.df_transport.iloc[0, col_index])
        
        # Conserve le préfixe '#' si le client est masqué
        if current_value.startswith("#"):
            self.df_transport.iloc[0, col_index] = f"#{new_demand}T"
        else:
            self.df_transport.iloc[0, col_index] = f"{new_demand}T"
            
        self._save_transport_data()

    def hide_clients(self, client_indices: list):
        """
        Masque un ou plusieurs clients en préfixant leur demande par '#'.
        Args:
            client_indices (list): Liste des index des clients à masquer.
        Returns:
            bool: True si au moins un client a été masqué, False sinon.
        Raises:
            IndexError: Si un index est hors limites.
            Exception: Pour les erreurs de sauvegarde.
        """
        if not client_indices:
            return False # Aucune sélection, rien à faire

        modified = False
        for idx in client_indices:
            if not (0 <= idx < len(self.get_client_actual_names())):
                raise IndexError(f"Index de client {idx} hors limites.")
            
            col_index = idx + 1
            original_value = str(self.df_transport.iloc[0, col_index])
            if not original_value.startswith("#"):
                self.df_transport.iloc[0, col_index] = f"#{original_value}"
                modified = True
        
        if modified:
            self._save_transport_data()
        return modified

    def add_new_client(self, quantite: int, couts: list, delai_max: int, delais_par_entrepot: list):
        """
        Ajoute un nouveau client au système, mettant à jour transport_temp.csv
        et delais_livraison.csv.

        Args:
            quantite (int): La quantité demandée par le nouveau client.
            couts (list): Liste des coûts de livraison depuis chaque entrepôt.
            delai_max (int): Le délai maximum accepté par ce client.
            delais_par_entrepot (list): Liste des délais de livraison proposés
                                        depuis chaque entrepôt pour ce client.

        Raises:
            ValueError: Si les valeurs sont invalides (non-numériques, négatives,
                        ou nombre incorrect de coûts/délais).
            FileNotFoundError: Si delais_livraison.csv est introuvable.
            Exception: Pour d'autres erreurs lors de l'ajout ou de la sauvegarde.
        """
        if not (isinstance(quantite, int) and quantite >= 0):
            raise ValueError("La quantité doit être un nombre entier non négatif.")
        if not (isinstance(delai_max, int) and delai_max >= 0):
            raise ValueError("Le délai max doit être un nombre entier non négatif.")
        if not all(isinstance(c, int) and c >= 0 for c in couts):
            raise ValueError("Tous les coûts doivent être des nombres entiers non négatifs.")
        if not all(isinstance(d, int) and d >= 0 for d in delais_par_entrepot):
            raise ValueError("Tous les délais par entrepôt doivent être des nombres entiers non négatifs.")

        nb_entrepots = len(self.df_transport.iloc[1:, 0]) # Nombre d'entrepôts dans transport_temp.csv

        if len(couts) != nb_entrepots:
            raise ValueError(f"Le nombre de coûts ({len(couts)}) ne correspond pas au nombre d'entrepôts ({nb_entrepots}).")
        if len(delais_par_entrepot) != nb_entrepots:
            raise ValueError(f"Le nombre de délais par entrepôt ({len(delais_par_entrepot)}) ne correspond pas au nombre d'entrepôts ({nb_entrepots}).")
        
        # Déterminer le nom du nouveau client (ex: Client 4, Client 5, etc.)
        # Basé sur le nombre de colonnes de clients déjà existantes (sans la première vide)
        new_client_id_num = self.df_transport.shape[1] - 1 # Nombre de clients existants (colonne 0 est vide)
        nouveau_nom_client = f"Client {new_client_id_num + 1}"

        # 1. Mise à jour de transport_temp.csv
        # La première ligne contient la demande du client, les autres les coûts des entrepôts
        nouvelle_colonne_transport = [f"{quantite}T"] + [f"{c}€" for c in couts]
        
        if len(nouvelle_colonne_transport) != self.df_transport.shape[0]:
            raise ValueError(f"La nouvelle colonne de transport a {len(nouvelle_colonne_transport)} éléments, mais le DataFrame de transport a {self.df_transport.shape[0]} lignes.")
        
        self.df_transport[nouveau_nom_client] = nouvelle_colonne_transport
        self._save_transport_data()

        # 2. Mise à jour de delais_livraison.csv
        # S'assurer que les lignes d'entrepôts et "Max_Delai_Client" existent
        # Nous rechargeons ici pour avoir la dernière version, si d'autres modifs ont eu lieu
        self.df_delais = self._load_delais_data()

        # Vérifier que toutes les lignes d'entrepôts et "Max_Delai_Client" existent
        expected_rows_delais = [f"Entrepot {i+1}" for i in range(nb_entrepots)] + ["Max_Delai_Client"]
        for row in expected_rows_delais:
            if row not in self.df_delais.index:
                raise ValueError(f"Ligne attendue '{row}' manquante dans '{self.delais_file}'. Veuillez vérifier le fichier.")
        
        # Ajouter la nouvelle colonne client dans delais_livraison.csv
        self.df_delais[nouveau_nom_client] = pd.NA # Utiliser pd.NA pour les nouvelles colonnes
        
        # Remplir les délais pour le nouveau client
        self.df_delais.at["Max_Delai_Client", nouveau_nom_client] = str(delai_max)
        for i in range(nb_entrepots):
            self.df_delais.at[f"Entrepot {i+1}", nouveau_nom_client] = str(delais_par_entrepot[i])
        
        self._save_delais_data()