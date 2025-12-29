""" Module de gestion des entrepôts pour la simulation de transport.
Ce module permet de gérer les opérations liées aux entrepôts,
y compris la lecture, l'écriture et la manipulation des données de transport et de délais.
Il inclut des fonctionnalités pour masquer les entrepôts, ajouter de nouveaux entrepôts,
et mettre à jour les stocks des entrepôts.
"""


import pandas as pd
import re
import os

# Constantes pour les noms de fichiers
TEMP_FILE = "transport_temp.csv"
DELAIS_FILE = "delais_livraison.csv"

def extraire_chiffre(cellule):
    """
    Extrait le premier nombre entier trouvé dans une chaîne de caractères.
    Retourne 0 si aucun nombre n'est trouvé.
    """
    match = re.search(r'\d+', str(cellule))
    return int(match.group()) if match else 0

class WarehouseManager:
    """
    Gère les opérations liées aux entrepôts, incluant la lecture,
    l'écriture et la manipulation des données de transport et de délais.
    """
    def __init__(self, temp_file=TEMP_FILE, delais_file=DELAIS_FILE):
        """
        Initialise le WarehouseManager en chargeant les données des fichiers CSV.

        Args:
            temp_file (str): Chemin vers le fichier des données de transport.
            delais_file (str): Chemin vers le fichier des données de délais de livraison.

        Raises:
            FileNotFoundError: Si l'un des fichiers n'est pas trouvé.
            Exception: Pour d'autres erreurs lors de la lecture des fichiers.
        """
        self.temp_file = temp_file
        self.delais_file = delais_file
        self.df_transport = self._load_transport_data()
        self.df_delais = self._load_delais_data() # Initialisation directe de df_delais

    def _load_transport_data(self):
        """
        Charge les données de transport depuis le fichier CSV spécifié.
        """
        if not os.path.exists(self.temp_file):
            raise FileNotFoundError(f"Le fichier de données '{self.temp_file}' est introuvable.")
        try:
            return pd.read_csv(self.temp_file, header=None)
        except Exception as e:
            raise Exception(f"Erreur lors de la lecture du fichier de transport '{self.temp_file}': {e}")

    def _load_delais_data(self):
        """
        Charge les données de délais depuis le fichier CSV spécifié.
        """
        if not os.path.exists(self.delais_file):
            raise FileNotFoundError(f"Le fichier des délais '{self.delais_file}' est introuvable.")
        try:
            # Assurez-vous que le séparateur est correct et l'index est la première colonne
            return pd.read_csv(self.delais_file, index_col=0, sep=',')
        except Exception as e:
            raise Exception(f"Erreur lors de la lecture du fichier des délais '{self.delais_file}': {e}")

    def _save_transport_data(self):
        """
        Sauvegarde le DataFrame de transport dans le fichier CSV.
        """
        try:
            self.df_transport.to_csv(self.temp_file, index=False, header=False)
        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde du fichier de transport '{self.temp_file}': {e}")

    def _save_delais_data(self):
        """
        Sauvegarde le DataFrame de délais dans le fichier CSV.
        """
        try:
            self.df_delais.to_csv(self.delais_file, index=True) # index=True car index_col=0 à la lecture
        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde du fichier des délais '{self.delais_file}': {e}")

    def get_warehouse_display_names(self):
        """
        Retourne une liste des noms d'affichage des entrepôts,
        indiquant si un entrepôt est masqué.
        """
        warehouse_stocks = self.df_transport.iloc[1:, 0].tolist()
        display_names = []
        for i, stock_value in enumerate(warehouse_stocks):
            prefix = "(masqué) " if str(stock_value).startswith("#") else ""
            display_names.append(f"{prefix}Entrepôt {i + 1}")
        return display_names

    def get_warehouse_actual_stocks(self):
        """
        Retourne une liste des valeurs de stock brutes (incluant le '#') des entrepôts.
        """
        return self.df_transport.iloc[1:, 0].tolist()

    def get_warehouse_stock_quantity(self, warehouse_index: int):
        """
        Retourne la quantité de stock d'un entrepôt spécifique, extrayant le chiffre.

        Args:
            warehouse_index (int): L'index de l'entrepôt (0-basé).

        Returns:
            int: La quantité de stock.

        Raises:
            IndexError: Si l'index de l'entrepôt est hors limites.
        """
        if not (0 <= warehouse_index < (self.df_transport.shape[0] - 1)):
            raise IndexError("Index d'entrepôt hors limites.")
        
        value = self.df_transport.iloc[warehouse_index + 1, 0]
        return extraire_chiffre(value)

    def update_warehouse_stock(self, warehouse_index: int, new_quantity: int):
        """
        Met à jour la quantité de stock d'un entrepôt spécifique.

        Args:
            warehouse_index (int): L'index de l'entrepôt (0-basé).
            new_quantity (int): La nouvelle quantité de stock (doit être non négative).

        Raises:
            ValueError: Si la nouvelle quantité n'est pas un entier non négatif.
            IndexError: Si l'index de l'entrepôt est hors limites.
        """
        if not isinstance(new_quantity, int) or new_quantity < 0:
            raise ValueError("La quantité doit être un nombre entier non négatif.")
        
        if not (0 <= warehouse_index < (self.df_transport.shape[0] - 1)):
            raise IndexError("Index d'entrepôt hors limites.")

        row_index = warehouse_index + 1
        current_value = str(self.df_transport.iloc[row_index, 0])
        
        if current_value.startswith("#"):
            self.df_transport.iloc[row_index, 0] = f"#{new_quantity}T"
        else:
            self.df_transport.iloc[row_index, 0] = f"{new_quantity}T"
            
        self._save_transport_data()

    def hide_warehouses(self, warehouse_indices: list):
        """
        Masque un ou plusieurs entrepôts en ajoutant un '#' devant leur stock.

        Args:
            warehouse_indices (list): Liste des index (0-basés) des entrepôts à masquer.

        Returns:
            bool: True si au moins un entrepôt a été masqué, False sinon.

        Raises:
            IndexError: Si un index d'entrepôt est hors limites.
        """
        if not warehouse_indices:
            return False

        modified = False
        for idx in warehouse_indices:
            if not (0 <= idx < (self.df_transport.shape[0] - 1)):
                raise IndexError(f"Index d'entrepôt {idx} hors limites.")
            
            row_index = idx + 1
            original_value = str(self.df_transport.iloc[row_index, 0])
            if not original_value.startswith("#"):
                self.df_transport.iloc[row_index, 0] = f"#{original_value}"
                modified = True
        
        if modified:
            self._save_transport_data()
        return modified

    def add_new_warehouse(self, stock_quantity: int, costs_to_clients: list, delays_to_clients: list):
        """
        Ajoute un nouvel entrepôt au système, mettant à jour transport_temp.csv
        et delais_livraison.csv.

        Args:
            stock_quantity (int): Le stock disponible pour le nouvel entrepôt.
            costs_to_clients (list): Liste des coûts de livraison depuis le nouvel entrepôt vers chaque client.
            delays_to_clients (list): Liste des délais de livraison proposés
                                       depuis le nouvel entrepôt vers chaque client.

        Raises:
            ValueError: Si les valeurs sont invalides (non-numériques, négatives,
                        ou nombre incorrect de coûts/délais, ou incohérence de fichiers).
            FileNotFoundError: Si delais_livraison.csv est introuvable (géré par _load_delais_data).
            Exception: Pour d'autres erreurs lors de l'ajout ou de la sauvegarde.
        """
        if not (isinstance(stock_quantity, int) and stock_quantity >= 0):
            raise ValueError("Le stock doit être un nombre entier non négatif.")
        if not all(isinstance(c, int) and c >= 0 for c in costs_to_clients):
            raise ValueError("Tous les coûts doivent être des nombres entiers non négatifs.")
        if not all(isinstance(d, int) and d >= 0 for d in delays_to_clients):
            raise ValueError("Tous les délais doivent être des nombres entiers non négatifs.")

        nb_clients = self.df_transport.shape[1] - 1 # Nombre de clients dans transport_temp.csv (colonnes après la première)

        if len(costs_to_clients) != nb_clients:
            raise ValueError(f"Le nombre de coûts ({len(costs_to_clients)}) ne correspond pas au nombre de clients ({nb_clients}).")
        if len(delays_to_clients) != nb_clients:
            raise ValueError(f"Le nombre de délais ({len(delays_to_clients)}) ne correspond pas au nombre de clients ({nb_clients}).")
        
        # 1. Mise à jour de transport_temp.csv
        nouvelle_ligne_transport = [f"{stock_quantity}T"] + [f"{c}€" for c in costs_to_clients]
        
        self.df_transport.loc[len(self.df_transport)] = nouvelle_ligne_transport
        self._save_transport_data()

        # 2. Mise à jour de delais_livraison.csv
        # Recharge df_delais pour avoir la version la plus récente si elle a été modifiée ailleurs
        # Note: self.df_delais est déjà initialisé, mais on le rafraîchit.
        df_delais_current = self._load_delais_data()
        
        # Déterminer le nom du nouvel entrepôt pour le fichier de délais
        # L'ID du nouvel entrepôt est le nombre total d'entrepôts après l'ajout dans transport_temp.csv.
        new_warehouse_id_num = self.df_transport.shape[0] - 1
        nom_nouvel_entrepot_delais = f"Entrepot {new_warehouse_id_num}"

        # Vérifier que le nom n'existe pas déjà (garde-fou)
        if nom_nouvel_entrepot_delais in df_delais_current.index:
             raise ValueError(f"L'entrepôt '{nom_nouvel_entrepot_delais}' existe déjà dans le fichier des délais.")
        
        # Vérifier que le nombre de colonnes clients dans df_delais_current correspond au nombre de clients
        client_names_delais = df_delais_current.columns.tolist()
        if len(client_names_delais) != nb_clients:
             raise ValueError(f"Le nombre de colonnes clients dans '{self.delais_file}' ({len(client_names_delais)}) ne correspond pas au nombre de clients dans '{self.temp_file}' ({nb_clients}).")

        # S'assurer que toutes les lignes d'entrepôts existantes et "Max_Delai_Client" existent.
        # Le nombre d'entrepôts attendus dans delais_livraison.csv pour les colonnes existantes
        # doit être le même que dans transport_temp.csv (avant l'ajout de la nouvelle ligne).
        nb_entrepots_initial = self.df_transport.shape[0] - 2
        
        expected_rows_delais = [f"Entrepot {i+1}" for i in range(nb_entrepots_initial)] + ["Max_Delai_Client"]
        for row in expected_rows_delais:
            if row not in df_delais_current.index:
                raise ValueError(f"Ligne attendue '{row}' manquante dans '{self.delais_file}'. Veuillez vérifier le fichier.")

        # Créer une nouvelle ligne pour le nouvel entrepôt dans df_delais_current
        df_delais_current.loc[nom_nouvel_entrepot_delais] = [pd.NA] * df_delais_current.shape[1]
        """        Remplir les délais pour le nouvel entrepôt.
        Pour chaque client, on remplit la colonne correspondante avec le délai spécifié.
        """

        # Remplir les délais pour le nouvel entrepôt
        for i in range(nb_clients):
            df_delais_current.at[nom_nouvel_entrepot_delais, client_names_delais[i]] = str(delays_to_clients[i])
            

        
        # Mettre à jour l'attribut self.df_delais avec le DataFrame modifié
        self.df_delais = df_delais_current
        self._save_delais_data()