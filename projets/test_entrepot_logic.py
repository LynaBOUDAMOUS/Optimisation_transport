"""
Module de test pour la logique de gestion des entrepôts (WarehouseManager)
et les fonctions associées, telles que 'extraire_chiffre'.

Ce module utilise Pytest pour tester les fonctionnalités de chargement,
modification et ajout de données d'entrepôts, ainsi que la gestion
des fichiers CSV sous-jacents.
"""

import pytest
import pandas as pd
import os
import csv
from unittest.mock import patch

# Importe les classes, fonctions et constantes du module 'warehouse_manager_logic' à tester.
from entrepot_logic import WarehouseManager, extraire_chiffre, TEMP_FILE, DELAIS_FILE

# --- Fixtures pour la configuration et le nettoyage des fichiers de test ---

@pytest.fixture(autouse=True)
def setup_teardown_test_files():
    """
    **Fixture Pytest** qui configure un environnement de test propre pour chaque test.
    Elle crée des fichiers CSV `transport_temp.csv` (pour les données de transport)
    et `delais_livraison.csv` (pour les données de délais) avec des données initiales
    avant l'exécution de chaque test, puis les supprime après.

    L'argument `autouse=True` signifie que cette fixture sera automatiquement
    appliquée à tous les tests dans ce module.
    """
    # Données initiales pour transport_temp.csv
    # La première ligne représente les demandes des clients.
    # Les lignes suivantes représentent les stocks des entrepôts (colonne 0) et les coûts de transport (col 1+).
    transport_data_initial = [
        ['', '50T', '30T', '20T'],  # Ligne 0: En-tête avec demandes clients (3 clients)
        ['10T', '2€', '3€', '4€'],  # Ligne 1: Entrepôt 1 (stock et coûts vers les 3 clients)
        ['5T', '1€', '4€', '3€'],   # Ligne 2: Entrepôt 2 (stock et coûts vers les 3 clients)
        ['20T', '5€', '2€', '1€'],  # Ligne 3: Entrepôt 3 (stock et coûts vers les 3 clients)
    ]
    # Note : Cette configuration implique 3 entrepôts (lignes 1, 2, 3) et 3 clients (colonnes 1, 2, 3).

    # Données initiales pour delais_livraison.csv (doivent correspondre aux entrepôts et clients ci-dessus)
    delais_data_initial = [
        ['', 'Client 1', 'Client 2', 'Client 3'], # En-tête pour les noms affichables des clients
        ['Entrepot 1', '2', '3', '1'],            # Délais pour Entrepot 1
        ['Entrepot 2', '4', '5', '2'],            # Délais pour Entrepot 2
        ['Entrepot 3', '1', '2', '3'],            # Délais pour Entrepot 3
        ['Max_Delai_Client', '3', '4', '2']       # Délais maximums acceptables par client
    ]

    # Écrit les données initiales dans transport_temp.csv
    with open(TEMP_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerows(transport_data_initial)

    # Écrit les données initiales dans delais_livraison.csv
    with open(DELAIS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerows(delais_data_initial)

    yield # Permet à Pytest d'exécuter le test après la configuration

    # --- Nettoyage après l'exécution de chaque test ---
    # Supprime les fichiers CSV temporaires pour garantir un environnement propre.
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
    if os.path.exists(DELAIS_FILE):
        os.remove(DELAIS_FILE)


## Tests pour la fonction `extraire_chiffre`

#Cette section contient les tests unitaires pour la fonction utilitaire `extraire_chiffre`, qui est chargée d'extraire le premier nombre entier d'une chaîne de caractères.



class TestExtraireChiffre:
    """
    Classe de tests pour la fonction autonome `extraire_chiffre`
    présente dans le module `warehouse_manager_logic`.
    """
    def test_extraire_chiffre_nombre_simple(self):
        """
        Teste l'extraction d'un nombre entier simple, seul dans une chaîne ou égal à zéro.
        """
        assert extraire_chiffre("123") == 123
        assert extraire_chiffre("0") == 0

    def test_extraire_chiffre_avec_texte(self):
        """
        Teste l'extraction de nombres lorsque la chaîne contient également du texte
        ou des préfixes/suffixes spécifiques ('T', '€', '#').
        La fonction doit toujours extraire le premier nombre trouvé.
        """
        assert extraire_chiffre("10T") == 10
        assert extraire_chiffre("#50T") == 50
        assert extraire_chiffre("Client 1") == 1
        assert extraire_chiffre("Entrepot 2") == 2

    def test_extraire_chiffre_sans_nombre(self):
        """
        Teste le comportement de la fonction lorsque la chaîne ne contient aucun nombre,
        est vide ou est `None`. Dans ces cas, la fonction doit retourner `0`.
        """
        assert extraire_chiffre("abc") == 0
        assert extraire_chiffre("") == 0
        assert extraire_chiffre(None) == 0



## Tests pour la classe `WarehouseManager`

#Cette section couvre les tests de la classe `WarehouseManager`, qui gère l'interaction avec les fichiers de données (transport et délais) et manipule les informations des entrepôts.



class TestWarehouseManager:
    """
    Classe de tests pour la classe `WarehouseManager`.
    Elle vérifie les fonctionnalités de chargement, lecture, mise à jour,
    masquage et ajout d'entrepôts.
    """
    def test_init_load_data_success(self):
        """
        Vérifie que le `WarehouseManager` charge les données correctement depuis
        `transport_temp.csv` et `delais_livraison.csv` lors de son initialisation.
        """
        manager = WarehouseManager()
        # Vérifie que les DataFrames ne sont pas vides après le chargement
        assert not manager.df_transport.empty
        assert not manager.df_delais.empty 
        # Vérifie que les chemins de fichiers sont correctement stockés
        assert manager.temp_file == TEMP_FILE
        assert manager.delais_file == DELAIS_FILE
        # Vérifie des valeurs spécifiques pour s'assurer du bon chargement et de la bonne structure
        assert manager.df_transport.iloc[1, 0] == '10T' # Stock de l'Entrepôt 1
        assert manager.df_transport.iloc[0, 1] == '50T' # Demande du Client 1
        # Vérifie une valeur dans le DataFrame des délais (convertie en chaîne pour la comparaison)
        assert str(manager.df_delais.loc['Entrepot 1', 'Client 1']) == '2' 

    def test_init_load_data_transport_file_not_found(self):
        """
        Vérifie qu'une `FileNotFoundError` est levée si le fichier `transport_temp.csv`
        est introuvable lors de l'initialisation du `WarehouseManager`.
        """
        os.remove(TEMP_FILE) # Supprime le fichier de transport pour simuler son absence
        with pytest.raises(FileNotFoundError, match=f"Le fichier de données '{TEMP_FILE}' est introuvable."):
            WarehouseManager()

    def test_init_load_data_delais_file_not_found(self):
        """
        Vérifie qu'une `FileNotFoundError` est levée si le fichier `delais_livraison.csv`
        est introuvable lors de l'initialisation du `WarehouseManager`.
        """
        os.remove(DELAIS_FILE) # Supprime le fichier de délais pour simuler son absence
        with pytest.raises(FileNotFoundError, match=f"Le fichier des délais '{DELAIS_FILE}' est introuvable."):
            WarehouseManager()

    def test_get_warehouse_display_names(self):
        """
        Vérifie que la méthode `get_warehouse_display_names` retourne les noms
        des entrepôts formatés pour l'affichage, incluant le préfixe '(masqué)'
        pour les entrepôts cachés.
        """
        manager = WarehouseManager()
        # Masque l'entrepôt à l'index 1 (qui correspond à 'Entrepot 2' dans le fichier delais_livraison.csv)
        manager.hide_warehouses([1]) 
        display_names = manager.get_warehouse_display_names()
        # Vérifie que les noms affichés sont corrects, avec le statut masqué appliqué.
        assert display_names == ['Entrepôt 1', '(masqué) Entrepôt 2', 'Entrepôt 3']

    def test_get_warehouse_actual_stocks(self):
        """
        Vérifie que la méthode `get_warehouse_actual_stocks` retourne les stocks réels
        des entrepôts tels qu'ils apparaissent dans la première colonne du fichier de transport,
        avec le préfixe '#' ajouté si un entrepôt est masqué.
        """
        manager = WarehouseManager()
        actual_stocks = manager.get_warehouse_actual_stocks()
        # Les stocks réels sont les valeurs de la première colonne (colonne 0)
        assert actual_stocks == ['10T', '5T', '20T']
        
        # Masque l'entrepôt à l'index 0 (qui correspond à '10T' dans le fichier transport)
        manager.hide_warehouses([0])
        actual_stocks_hidden = manager.get_warehouse_actual_stocks()
        # Vérifie que le préfixe '#' est ajouté à la valeur masquée
        assert actual_stocks_hidden == ['#10T', '5T', '20T']

    def test_get_warehouse_stock_quantity_success(self):
        """
        Teste la récupération réussie de la quantité de stock d'un entrepôt par son index.
        """
        manager = WarehouseManager()
        # Vérifie les quantités de stock des entrepôts aux indices 0, 1 et 2
        assert manager.get_warehouse_stock_quantity(0) == 10
        assert manager.get_warehouse_stock_quantity(1) == 5
        assert manager.get_warehouse_stock_quantity(2) == 20

    def test_get_warehouse_stock_quantity_index_out_of_bounds(self):
        """
        Teste la gestion des erreurs lorsque l'index fourni à `get_warehouse_stock_quantity`
        est hors des limites valides.
        """
        manager = WarehouseManager()
        # Vérifie qu'une `IndexError` est levée pour un index trop grand
        with pytest.raises(IndexError, match="Index d'entrepôt hors limites."):
            manager.get_warehouse_stock_quantity(99)
        # Vérifie qu'une `IndexError` est levée pour un index négatif
        with pytest.raises(IndexError, match="Index d'entrepôt hors limites."):
            manager.get_warehouse_stock_quantity(-1)

    def test_update_warehouse_stock_success(self):
        """
        Teste la mise à jour réussie de la quantité de stock d'un entrepôt dans le DataFrame
        et la persistance de cette modification dans le fichier CSV.
        """
        manager = WarehouseManager()
        manager.update_warehouse_stock(0, 99) # Met à jour le stock de l'Entrepôt 1 à 99
        
        # Recharge le fichier CSV pour vérifier la persistance de la modification
        df_updated = pd.read_csv(TEMP_FILE, header=None)
        assert df_updated.iloc[1, 0] == '99T'
        assert df_updated.iloc[2, 0] == '5T' # Vérifie que les autres stocks ne sont pas affectés

        # Teste la mise à jour d'un entrepôt qui a été masqué
        manager.hide_warehouses([1]) # Masque l'Entrepôt 2 (qui est '5T')
        manager.update_warehouse_stock(1, 100) # Modifie le stock de l'Entrepôt 2 à 100
        df_updated_hidden = pd.read_csv(TEMP_FILE, header=None)
        # Vérifie que le préfixe '#' est conservé après la mise à jour
        assert df_updated_hidden.iloc[2, 0] == '#100T'

    def test_update_warehouse_stock_invalid_value(self):
        """
        Teste la gestion des valeurs invalides (non numériques, négatives)
        lors de la tentative de mise à jour du stock d'un entrepôt.
        """
        manager = WarehouseManager()
        # Vérifie qu'une `ValueError` est levée pour une valeur non numérique
        with pytest.raises(ValueError, match="La quantité doit être un nombre entier non négatif."):
            manager.update_warehouse_stock(0, "abc")
        # Vérifie qu'une `ValueError` est levée pour une valeur négative
        with pytest.raises(ValueError, match="La quantité doit être un nombre entier non négatif."):
            manager.update_warehouse_stock(0, -10)
        
        # Vérifie que le fichier CSV n'a pas été modifié suite aux tentatives invalides
        df_original = pd.read_csv(TEMP_FILE, header=None)
        assert df_original.iloc[1, 0] == '10T' # La valeur doit être restée à son état initial

    def test_update_warehouse_stock_index_out_of_bounds(self):
        """
        Teste la gestion des erreurs lorsque l'index fourni à `update_warehouse_stock`
        est hors des limites valides.
        """
        manager = WarehouseManager()
        with pytest.raises(IndexError, match="Index d'entrepôt hors limites."):
            manager.update_warehouse_stock(99, 10) # Tente de modifier un entrepôt avec un index inexistant

    def test_hide_warehouses_success(self):
        """
        Teste le masquage réussi d'un ou plusieurs entrepôts, et la persistance
        de cette modification dans le fichier CSV.
        """
        manager = WarehouseManager()
        # Masque un seul entrepôt (Entrepôt 1 à l'index 0)
        result = manager.hide_warehouses([0])
        assert result is True # La fonction doit indiquer qu'une modification a eu lieu
        df_updated = pd.read_csv(TEMP_FILE, header=None)
        assert df_updated.iloc[1, 0] == '#10T' # Vérifie le préfixe '#'
        assert df_updated.iloc[2, 0] == '5T' # Vérifie que l'autre entrepôt n'est pas affecté

        # Réinitialise le fichier de transport pour un nouveau test de masquage multiple
        transport_data_initial_reset = [
            ['', '50T', '30T', '20T'],
            ['10T', '2€', '3€', '4€'],
            ['5T', '1€', '4€', '3€'],
            ['20T', '5€', '2€', '1€'],
        ]
        with open(TEMP_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(transport_data_initial_reset)
        manager = WarehouseManager() # Recharge le manager pour refléter le fichier réinitialisé
        
        # Masque plusieurs entrepôts (Entrepôt 1 et Entrepôt 3)
        result_multiple = manager.hide_warehouses([0, 2])
        assert result_multiple is True
        df_updated_multiple = pd.read_csv(TEMP_FILE, header=None)
        assert df_updated_multiple.iloc[1, 0] == '#10T'
        assert df_updated_multiple.iloc[2, 0] == '5T' # Entrepôt 2 n'est pas masqué
        assert df_updated_multiple.iloc[3, 0] == '#20T'

    def test_hide_warehouses_already_hidden(self):
        """
        Teste le comportement lorsque l'on tente de masquer un entrepôt déjà masqué.
        La fonction ne devrait rien modifier et retourner `False`.
        """
        manager = WarehouseManager()
        manager.hide_warehouses([0]) # Masque l'Entrepôt 1 une première fois
        
        result = manager.hide_warehouses([0]) # Tente de le masquer à nouveau
        assert result is False # Indique qu'aucune nouvelle modification n'a été faite

        df_updated = pd.read_csv(TEMP_FILE, header=None)
        assert df_updated.iloc[1, 0] == '#10T' # La valeur doit rester inchangée avec le préfixe

    def test_hide_warehouses_no_selection(self):
        """
        Teste le comportement lorsque la liste des entrepôts à masquer est vide.
        Aucune modification ne devrait être effectuée et la fonction doit retourner `False`.
        """
        manager = WarehouseManager()
        result = manager.hide_warehouses([]) # Tente de masquer une liste vide d'entrepôts
        assert result is False # Indique qu'aucune modification n'a été faite

        df_original = pd.read_csv(TEMP_FILE, header=None)
        assert df_original.iloc[1, 0] == '10T' # Le fichier ne doit pas avoir changé

    def test_hide_warehouses_index_out_of_bounds(self):
        """
        Teste la gestion des erreurs lorsque la liste des entrepôts à masquer contient
        un index hors des limites valides.
        """
        manager = WarehouseManager()
        with pytest.raises(IndexError, match="Index d'entrepôt 99 hors limites."):
            manager.hide_warehouses([0, 99]) # Tente de masquer avec un index valide et un invalide

    def test_add_new_warehouse_success(self):
        """
        Teste l'ajout réussi d'un nouvel entrepôt (stock, coûts vers clients, délais vers clients)
        et vérifie que les deux fichiers CSV (`transport_temp.csv` et `delais_livraison.csv`)
        sont correctement mis à jour.
        """
        manager = WarehouseManager()
        initial_rows_transport = manager.df_transport.shape[0] # Nombre initial de lignes dans transport_temp
        initial_rows_delais = manager.df_delais.shape[0]       # Nombre initial de lignes dans delais_livraison
        initial_cols_delais = manager.df_delais.shape[1]       # Nombre initial de colonnes dans delais_livraison (nb clients + 1)

        # Données du nouvel entrepôt
        stock_quantity = 150
        costs_to_clients = [10, 20, 30]  # Doit correspondre au nombre de clients (3)
        delays_to_clients = [2, 3, 4]    # Doit correspondre au nombre de clients (3)

        manager.add_new_warehouse(stock_quantity, costs_to_clients, delays_to_clients)

        # --- Vérification de `transport_temp.csv` ---
        df_transport_updated = pd.read_csv(TEMP_FILE, header=None)
        # Vérifie qu'une nouvelle ligne a été ajoutée
        assert df_transport_updated.shape[0] == initial_rows_transport + 1
        new_warehouse_row_index = initial_rows_transport # L'index de la nouvelle ligne d'entrepôt
        
        # Vérifie que les données du nouvel entrepôt sont correctement insérées
        assert df_transport_updated.iloc[new_warehouse_row_index, 0] == f"{stock_quantity}T"
        assert df_transport_updated.iloc[new_warehouse_row_index, 1] == f"{costs_to_clients[0]}€"
        assert df_transport_updated.iloc[new_warehouse_row_index, 2] == f"{costs_to_clients[1]}€"
        assert df_transport_updated.iloc[new_warehouse_row_index, 3] == f"{costs_to_clients[2]}€"
        
        # --- Vérification de `delais_livraison.csv` ---
        df_delais_updated = pd.read_csv(DELAIS_FILE, index_col=0, sep=',')
        # Vérifie qu'une nouvelle ligne a été ajoutée (avant la ligne 'Max_Delai_Client')
        assert df_delais_updated.shape[0] == initial_rows_delais + 1 
        # Vérifie que le nombre de colonnes clients est inchangé
        assert df_delais_updated.shape[1] == initial_cols_delais 

        # Génère le nom attendu pour le nouvel entrepôt dans le fichier de délais
        # L'ID de l'entrepôt est basé sur l'index de la ligne dans le fichier transport, en partant de 1.
        new_warehouse_name_delais = f"Entrepot {new_warehouse_row_index}" 

        # Vérifie que les délais du nouvel entrepôt sont correctement insérés
        assert int(df_delais_updated.loc[new_warehouse_name_delais, 'Client 1']) == delays_to_clients[0]
        assert int(df_delais_updated.loc[new_warehouse_name_delais, 'Client 2']) == delays_to_clients[1]
        assert int(df_delais_updated.loc[new_warehouse_name_delais, 'Client 3']) == delays_to_clients[2]


    @pytest.mark.parametrize("stock_quantity, costs, delays, error_match", [
        ("abc", [1,2,3], [1,2,3], "Le stock doit être un nombre entier non négatif."), # Stock invalide
        (10, [1,"b",3], [1,2,3], "Tous les coûts doivent être des nombres entiers non négatifs."), # Coût invalide
        (10, [1,2,3], [1,"d",3], "Tous les délais doivent être des nombres entiers non négatifs."), # Délai invalide
        (10, [1,2], [1,2,3], r"Le nombre de coûts \(2\) ne correspond pas au nombre de clients \(3\)."), # Nombre de coûts incorrect
        (10, [1,2,3], [1,2], r"Le nombre de délais \(2\) ne correspond pas au nombre de clients \(3\)."), # Nombre de délais incorrect
    ])
    def test_add_new_warehouse_invalid_inputs(self, stock_quantity, costs, delays, error_match):
        """
        Teste la fonction `add_new_warehouse` avec divers types d'entrées invalides.
        Vérifie qu'une `ValueError` est levée avec le message d'erreur approprié
        et que les fichiers CSV ne sont pas modifiés.
        """
        manager = WarehouseManager()
        initial_rows_transport = manager.df_transport.shape[0]
        initial_rows_delais = manager.df_delais.shape[0]

        with pytest.raises(ValueError, match=error_match):
            manager.add_new_warehouse(stock_quantity, costs, delays)

        # Vérifie que la forme des DataFrames n'a pas changé (pas d'ajout de ligne)
        df_transport_original = pd.read_csv(TEMP_FILE, header=None)
        assert df_transport_original.shape[0] == initial_rows_transport
        df_delais_original = pd.read_csv(DELAIS_FILE, index_col=0, sep=',')
        assert df_delais_original.shape[0] == initial_rows_delais

    def test_add_new_warehouse_missing_delais_row(self):
        """
        Teste le cas où une ligne d'entrepôt est manquante dans `delais_livraison.csv`,
        ce qui empêcherait l'ajout correct d'un nouvel entrepôt.
        """
        # Modifie le fichier de délais pour qu'il soit incomplet (manque Entrepot 3)
        delais_data_incomplete = [
            ['', 'Client 1', 'Client 2', 'Client 3'],
            ['Entrepot 1', '2', '3', '1'],
            ['Entrepot 2', '4', '5', '2'],
            # 'Entrepot 3' est délibérément manquante ici
            ['Max_Delai_Client', '3', '4', '2']
        ]
        with open(DELAIS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(delais_data_incomplete)

        # Recharge le manager pour qu'il utilise le fichier de délais modifié
        manager = WarehouseManager()
        
        # Données pour le nouvel entrepôt
        stock_quantity = 150
        costs = [10, 20, 30]
        delays = [2, 3, 4]

        # S'attend à une `ValueError` indiquant la ligne manquante
        with pytest.raises(ValueError, match=r"Ligne attendue 'Entrepot 3' manquante dans 'delais_livraison.csv'."):
            manager.add_new_warehouse(stock_quantity, costs, delays)
            
    def test_add_new_warehouse_delais_client_columns_mismatch(self):
        """
        Teste le cas où `delais_livraison.csv` n'a pas le même nombre de colonnes clients
        que `transport_temp.csv`, ce qui est une incohérence de données.
        """
        # Modifie `delais_livraison.csv` pour avoir moins de clients que `transport_temp.csv`
        # `transport_temp.csv` (via la fixture) a 3 clients, ce fichier en aura 2.
        delais_data_mismatch_cols = [
            ['', 'Client 1', 'Client 2'], # Manque Client 3
            ['Entrepot 1', '2', '3'],
            ['Entrepot 2', '4', '5'],
            ['Entrepot 3', '1', '2'],
            ['Max_Delai_Client', '3', '4']
        ]
        with open(DELAIS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(delais_data_mismatch_cols)
        
        # Recharge le manager pour qu'il prenne en compte le fichier de délais modifié
        manager = WarehouseManager()
        
        # Données pour le nouvel entrepôt. Les coûts et délais sont pour 3 clients,
        # alors que le fichier delais_livraison n'en a que 2.
        stock_quantity = 150
        costs = [10, 20, 30] 
        delays = [2, 3, 4]

        # Le message d'erreur attendu pour le décalage du nombre de colonnes clients
        expected_error_message = r"Le nombre de colonnes clients dans 'delais_livraison.csv' \(2\) ne correspond pas au nombre de clients dans 'transport_temp.csv' \(3\)."
        
        with pytest.raises(ValueError, match=expected_error_message):
            manager.add_new_warehouse(stock_quantity, costs, delays)

    if __name__ == "__main__":
        # Permet d'exécuter les tests directement depuis ce fichier.
        # C'est pratique pour le débogage ou l'exécution rapide.
        pytest.main([__file__])