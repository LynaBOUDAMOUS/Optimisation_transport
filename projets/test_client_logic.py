"""
Module de test pour la logique de gestion des clients (ClientManager)
et les fonctions associées, telles que 'extraire_chiffre'.

Ce module utilise Pytest pour tester les fonctionnalités de chargement,
modification et ajout de données clients et entrepôts, ainsi que la gestion
des fichiers CSV sous-jacents.
"""

import pytest
import pandas as pd
import os
import csv
from unittest.mock import patch, mock_open

# Importe les classes, fonctions et constantes du module 'client_manager_logic' à tester.
from client_logic import ClientManager, extraire_chiffre, TEMP_FILE, DELAIS_FILE

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
    # La première ligne représente les demandes des clients (colonne vide, puis 'XXT').
    # Les lignes suivantes représentent les stocks des entrepôts (colonne 0) et les coûts de transport (col 1+).
    transport_data_initial = [
        ['', '50T', '30T', '20T'],  # En-tête avec demandes clients
        ['10T', '2€', '3€', '4€'],  # Offre Entrepot 1 et coûts vers clients
        ['5T', '1€', '4€', '3€'],   # Offre Entrepot 2 et coûts vers clients
        ['20T', '5€', '2€', '1€'],  # Offre Entrepot 3 et coûts vers clients
    ]
    # Note : Cette configuration implique 3 entrepôts (lignes 1, 2, 3) et 3 clients (colonnes 1, 2, 3).

    # Données initiales pour delais_livraison.csv (doivent correspondre aux entrepôts et clients ci-dessus)
    delais_data_initial = [
        ['', 'Client 1', 'Client 2', 'Client 3'], # En-tête pour les noms affichables des clients
        ['Entrepot 1', '2', '3', '1'],            # Délais pour Entrepot 1
        ['Entrepot 2', '4', '5', '2'],            # Délais pour Entrepot 2
        ['Entrepot 3', '1', '2', '3'],            # Délais pour Entrepot 3 (pour correspondre aux 3 entrepôts)
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
    présente dans le module `client_manager_logic`.
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



## Tests pour la classe `ClientManager`

#Cette section couvre les tests de la classe `ClientManager`, qui gère l'interaction avec les fichiers de données (transport et délais) et manipule les informations des clients et entrepôts.



class TestClientManager:
    """
    Classe de tests pour la classe `ClientManager`.
    Elle vérifie les fonctionnalités de chargement, lecture, mise à jour,
    masquage et ajout de clients et entrepôts.
    """
    def test_init_load_data_success(self):
        """
        Vérifie que le `ClientManager` charge les données correctement depuis
        `transport_temp.csv` et `delais_livraison.csv` lors de son initialisation.
        """
        manager = ClientManager()
        # Vérifie que les DataFrames ne sont pas vides après le chargement
        assert not manager.df_transport.empty
        assert not manager.df_delais.empty
        # Vérifie des valeurs spécifiques pour s'assurer du bon chargement et de la bonne structure
        assert manager.df_transport.iloc[0, 1] == '50T' # Demande du Client 1 (première cellule de données)
        assert manager.df_transport.iloc[0, 3] == '20T' # Demande du Client 3
        assert manager.df_transport.iloc[1, 0] == '10T' # Stock de l'Entrepôt 1
        # Vérifie une valeur dans le DataFrame des délais (conversion en int pour la comparaison)
        assert int(manager.df_delais.loc['Entrepot 1', 'Client 1']) == 2

    def test_init_load_data_transport_file_not_found(self):
        """
        Vérifie qu'une `FileNotFoundError` est levée si le fichier `transport_temp.csv`
        est introuvable lors de l'initialisation du `ClientManager`.
        """
        os.remove(TEMP_FILE) # Supprime le fichier de transport pour simuler son absence
        with pytest.raises(FileNotFoundError, match=f"Le fichier de données '{TEMP_FILE}' est introuvable."):
            ClientManager()

    def test_init_load_data_delais_file_not_found(self):
        """
        Vérifie qu'une `FileNotFoundError` est levée si le fichier `delais_livraison.csv`
        est introuvable lors de l'initialisation du `ClientManager`.
        """
        os.remove(DELAIS_FILE) # Supprime le fichier de délais pour simuler son absence
        with pytest.raises(FileNotFoundError, match=f"Le fichier des délais '{DELAIS_FILE}' est introuvable."):
            ClientManager()

    def test_get_client_display_names(self):
        """
        Vérifie que la méthode `get_client_display_names` retourne les noms
        des clients formatés pour l'affichage, incluant le préfixe '(masqué)'
        pour les clients cachés.
        """
        manager = ClientManager()
        # Masque le client à l'index 1 (qui correspond à 'Client 2' dans le fichier delais_livraison.csv)
        manager.hide_clients([1])
        
        display_names = manager.get_client_display_names()
        # Vérifie que les noms affichés sont corrects, avec le statut masqué appliqué.
        assert display_names == ['Client 1', '(masqué) Client 2', 'Client 3']

    def test_get_client_actual_names(self):
        """
        Vérifie que la méthode `get_client_actual_names` retourne les noms réels
        des clients tels qu'ils apparaissent dans la première ligne du fichier de transport,
        avec le préfixe '#' ajouté si un client est masqué.
        """
        manager = ClientManager()
        actual_names = manager.get_client_actual_names()
        # Les noms réels sont les demandes de la première ligne
        assert actual_names == ['50T', '30T', '20T'] 
        
        # Masque le client à l'index 1 (correspondant à '30T' dans le fichier transport)
        manager.hide_clients([1])
        actual_names_hidden = manager.get_client_actual_names()
        # Vérifie que le préfixe '#' est ajouté à la valeur masquée
        assert actual_names_hidden == ['50T', '#30T', '20T']

    def test_get_client_demand_success(self):
        """
        Teste la récupération réussie de la demande d'un client par son index.
        """
        manager = ClientManager()
        # Vérifie les demandes des clients aux indices 0, 1 et 2
        assert manager.get_client_demand(0) == 50
        assert manager.get_client_demand(1) == 30
        assert manager.get_client_demand(2) == 20

    def test_get_client_demand_index_out_of_bounds(self):
        """
        Teste la gestion des erreurs lorsque l'index fourni à `get_client_demand`
        est hors des limites valides.
        """
        manager = ClientManager()
        # Vérifie qu'une `IndexError` est levée pour un index trop grand
        with pytest.raises(IndexError, match="Index de client hors limites."):
            manager.get_client_demand(99)
        # Vérifie qu'une `IndexError` est levée pour un index négatif
        with pytest.raises(IndexError, match="Index de client hors limites."):
            manager.get_client_demand(-1)

    def test_update_client_demand_success(self):
        """
        Teste la mise à jour réussie de la demande d'un client dans le DataFrame
        et la persistance de cette modification dans le fichier CSV.
        """
        manager = ClientManager()

        manager.update_client_demand(0, 75) # Met à jour la demande du Client 1 à 75
        
        # Recharge le fichier CSV pour vérifier la persistance de la modification
        df_updated = pd.read_csv(TEMP_FILE, header=None)
        assert df_updated.iloc[0, 1] == '75T'
        assert df_updated.iloc[0, 2] == '30T' # Vérifie que les autres demandes ne sont pas affectées

        # Teste la mise à jour d'un client qui a été masqué
        manager.hide_clients([1]) # Masque le Client 2 (qui est '30T')
        manager.update_client_demand(1, 100) # Modifie la demande du Client 2 à 100
        df_updated_hidden = pd.read_csv(TEMP_FILE, header=None)
        # Vérifie que le préfixe '#' est conservé après la mise à jour
        assert df_updated_hidden.iloc[0, 2] == '#100T'

    def test_update_client_demand_invalid_value(self):
        """
        Teste la gestion des valeurs invalides (non numériques, négatives)
        lors de la tentative de mise à jour de la demande d'un client.
        """
        manager = ClientManager()
        # Vérifie qu'une `ValueError` est levée pour une valeur non numérique
        with pytest.raises(ValueError, match="La demande doit être un nombre entier non négatif."):
            manager.update_client_demand(0, "abc")
        # Vérifie qu'une `ValueError` est levée pour une valeur négative
        with pytest.raises(ValueError, match="La demande doit être un nombre entier non négatif."):
            manager.update_client_demand(0, -10)
        
        # Vérifie que le fichier CSV n'a pas été modifié suite aux tentatives invalides
        df_original = pd.read_csv(TEMP_FILE, header=None)
        assert df_original.iloc[0, 1] == '50T' # La valeur doit être restée à son état initial

    def test_update_client_demand_index_out_of_bounds(self):
        """
        Teste la gestion des erreurs lorsque l'index fourni à `update_client_demand`
        est hors des limites valides.
        """
        manager = ClientManager()
        with pytest.raises(IndexError, match="Index de client hors limites."):
            manager.update_client_demand(99, 10) # Tente de modifier un client avec un index inexistant

    def test_hide_clients_success(self):
        """
        Teste le masquage réussi d'un ou plusieurs clients, et la persistance
        de cette modification dans le fichier CSV.
        """
        manager = ClientManager()
        # Masque un seul client (Client 1 à l'index 0)
        result = manager.hide_clients([0])
        assert result is True # La fonction doit indiquer qu'une modification a eu lieu
        df_updated = pd.read_csv(TEMP_FILE, header=None)
        assert df_updated.iloc[0, 1] == '#50T' # Vérifie le préfixe '#'
        assert df_updated.iloc[0, 2] == '30T' # Vérifie que l'autre client n'est pas affecté

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
        manager = ClientManager() # Recharge le manager pour refléter le fichier réinitialisé
        
        # Masque plusieurs clients (Client 1 et Client 3)
        result_multiple = manager.hide_clients([0, 2])
        assert result_multiple is True
        df_updated_multiple = pd.read_csv(TEMP_FILE, header=None)
        assert df_updated_multiple.iloc[0, 1] == '#50T'
        assert df_updated_multiple.iloc[0, 2] == '30T' # Client 2 n'est pas masqué
        assert df_updated_multiple.iloc[0, 3] == '#20T'

    def test_hide_clients_already_hidden(self):
        """
        Teste le comportement lorsque l'on tente de masquer un client déjà masqué.
        La fonction ne devrait rien modifier et retourner `False`.
        """
        manager = ClientManager()
        manager.hide_clients([0]) # Masque le Client 1 une première fois
        
        result = manager.hide_clients([0]) # Tente de le masquer à nouveau
        assert result is False # Indique qu'aucune nouvelle modification n'a été faite

        df_updated = pd.read_csv(TEMP_FILE, header=None)
        assert df_updated.iloc[0, 1] == '#50T' # La valeur doit rester inchangée avec le préfixe

    def test_hide_clients_no_selection(self):
        """
        Teste le comportement lorsque la liste des clients à masquer est vide.
        Aucune modification ne devrait être effectuée et la fonction doit retourner `False`.
        """
        manager = ClientManager()
        result = manager.hide_clients([]) # Tente de masquer une liste vide de clients
        assert result is False # Indique qu'aucune modification n'a été faite

        df_original = pd.read_csv(TEMP_FILE, header=None)
        assert df_original.iloc[0, 1] == '50T' # Le fichier ne doit pas avoir changé

    def test_hide_clients_index_out_of_bounds(self):
        """
        Teste la gestion des erreurs lorsque la liste des clients à masquer contient
        un index hors des limites valides.
        """
        manager = ClientManager()
        with pytest.raises(IndexError, match="Index de client 99 hors limites."):
            manager.hide_clients([0, 99]) # Tente de masquer avec un index valide et un invalide

    def test_add_new_client_success(self):
        """
        Teste l'ajout réussi d'un nouveau client (demande, coûts de transport, délais)
        et vérifie que les deux fichiers CSV (`transport_temp.csv` et `delais_livraison.csv`)
        sont correctement mis à jour.
        """
        manager = ClientManager()
        initial_cols_transport = manager.df_transport.shape[1] # Nombre initial de colonnes dans transport_temp
        initial_cols_delais = manager.df_delais.shape[1]       # Nombre initial de colonnes dans delais_livraison

        # Données du nouveau client
        quantite = 150
        couts = [10, 20, 30] # Doit correspondre au nombre d'entrepôts dans la fixture (3)
        delai_max = 5
        delais_par_entrepot = [2, 3, 4] # Doit correspondre au nombre d'entrepôts dans la fixture (3)

        manager.add_new_client(quantite, couts, delai_max, delais_par_entrepot)

        # --- Vérification de `transport_temp.csv` ---
        df_transport_updated = pd.read_csv(TEMP_FILE, header=None)
        # Vérifie qu'une nouvelle colonne a été ajoutée
        assert df_transport_updated.shape[1] == initial_cols_transport + 1
        new_client_col_index = initial_cols_transport # L'index de la nouvelle colonne client
        
        # Vérifie que les données du nouveau client sont correctement insérées
        assert df_transport_updated.iloc[0, new_client_col_index] == f"{quantite}T"
        assert df_transport_updated.iloc[1, new_client_col_index] == f"{couts[0]}€"
        assert df_transport_updated.iloc[2, new_client_col_index] == f"{couts[1]}€"
        assert df_transport_updated.iloc[3, new_client_col_index] == f"{couts[2]}€" # Pour le 3ème entrepôt
        
        # --- Vérification de `delais_livraison.csv` ---
        df_delais_updated = pd.read_csv(DELAIS_FILE, index_col=0, sep=',')
        # Vérifie qu'une nouvelle colonne a été ajoutée
        assert df_delais_updated.shape[1] == initial_cols_delais + 1
        # Génère le nom attendu pour le nouveau client dans le fichier de délais
        new_client_name = f"Client {new_client_col_index}" 
        
        # Vérifie que les délais du nouveau client sont correctement insérés
        assert int(df_delais_updated.loc['Max_Delai_Client', new_client_name]) == delai_max
        assert int(df_delais_updated.loc['Entrepot 1', new_client_name]) == delais_par_entrepot[0]
        assert int(df_delais_updated.loc['Entrepot 2', new_client_name]) == delais_par_entrepot[1]
        assert int(df_delais_updated.loc['Entrepot 3', new_client_name]) == delais_par_entrepot[2]

    @pytest.mark.parametrize("quantite, couts, delai_max, delais_par_entrepot, error_match", [
        ("abc", [1,2,3], 1, [1,2,3], "La quantité doit être un nombre entier non négatif."), # Quantité invalide
        (10, [1,"b",3], 1, [1,2,3], "Tous les coûts doivent être des nombres entiers non négatifs."), # Coût invalide
        (10, [1,2,3], "xyz", [1,2,3], "Le délai max doit être un nombre entier non négatif."), # Délai max invalide
        (10, [1,2,3], 1, [1,"d",3], "Tous les délais par entrepôt doivent être des nombres entiers non négatifs."), # Délai par entrepôt invalide
        (10, [1,2], 1, [1,2,3], r"Le nombre de coûts \(2\) ne correspond pas au nombre d'entrepôts \(3\)."), # Nombre de coûts incorrect
        (10, [1,2,3], 1, [1,2], r"Le nombre de délais par entrepôt \(2\) ne correspond pas au nombre d'entrepôts \(3\)."), # Nombre de délais incorrect
    ])
    def test_add_new_client_invalid_inputs(self, quantite, couts, delai_max, delais_par_entrepot, error_match):
        """
        Teste la fonction `add_new_client` avec divers types d'entrées invalides.
        Vérifie qu'une `ValueError` est levée avec le message d'erreur approprié
        et que les fichiers CSV ne sont pas modifiés.
        """
        manager = ClientManager()
        initial_cols_transport = manager.df_transport.shape[1]
        initial_cols_delais = manager.df_delais.shape[1]

        with pytest.raises(ValueError, match=error_match):
            manager.add_new_client(quantite, couts, delai_max, delais_par_entrepot)

        # Vérifie que la forme des DataFrames n'a pas changé (pas d'ajout de colonne)
        df_transport_original = pd.read_csv(TEMP_FILE, header=None)
        assert df_transport_original.shape[1] == initial_cols_transport
        df_delais_original = pd.read_csv(DELAIS_FILE, index_col=0, sep=',')
        assert df_delais_original.shape[1] == initial_cols_delais

    def test_add_new_client_missing_delais_row(self):
        """
        Teste le cas où une ligne essentielle (comme `Max_Delai_Client` ou un `Entrepot X`)
        est manquante dans le fichier `delais_livraison.csv`, ce qui empêcherait l'ajout correct
        d'un nouveau client.
        """
        # Modifie le fichier de délais pour le rendre incomplet
        delais_data_incomplete = [
            ['', 'Client 1', 'Client 2', 'Client 3'],
            ['Entrepot 1', '2', '3', '1'],
            ['Entrepot 2', '4', '5', '2'],
            # 'Entrepot 3' et 'Max_Delai_Client' sont délibérément manquants ici
        ]
        with open(DELAIS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(delais_data_incomplete)

        # Recharge le manager pour qu'il utilise le fichier de délais modifié
        manager = ClientManager()
        
        # Données pour le nouveau client
        quantite = 150
        couts = [10, 20, 30] # On s'attend toujours à 3 entrepôts (basé sur `transport_temp.csv` initial)
        delai_max = 5
        delais_par_entrepot = [2, 3, 4]

        # S'attend à une `ValueError` indiquant la ligne manquante
        with pytest.raises(ValueError, match=r"Ligne attendue 'Entrepot 3' manquante dans 'delais_livraison.csv'."):
            manager.add_new_client(quantite, couts, delai_max, delais_par_entrepot)

    def test_add_new_client_transport_data_shape_mismatch(self):
        """
        Teste le scénario où le nombre de coûts ou de délais fournis ne correspond
        pas au nombre d'entrepôts *réellement* chargés depuis `transport_temp.csv`
        (si ce dernier a été modifié pour avoir un nombre différent d'entrepôts).
        """
        # Modifie `transport_temp.csv` pour n'avoir qu'un seul entrepôt
        transport_data_mismatch = [
            ['', 'Client 1'],
            ['10T', '2€'], # Un seul entrepôt ici
        ]
        with open(TEMP_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(transport_data_mismatch)
        
        # Recharge le manager pour qu'il prenne en compte le fichier de transport modifié
        manager = ClientManager() 
        
        # Données pour le nouveau client. On fournit 3 coûts/délais,
        # mais le manager ne voit qu'un entrepôt.
        quantite = 150
        couts = [10, 20, 30] 
        delai_max = 5
        delais_par_entrepot = [2, 3, 4]

        # S'attend à une `ValueError` car le nombre d'entrées fournies ne correspond pas au nombre d'entrepôts détecté.
        # Le message d'erreur inclura le nombre attendu d'entrepôts (1 dans ce cas).
        with pytest.raises(ValueError, match=r"Le nombre de coûts \(3\) ne correspond pas au nombre d'entrepôts \(1\)\."):
            manager.add_new_client(quantite, couts, delai_max, delais_par_entrepot)

    if __name__ == "__main__":
        # Permet d'exécuter les tests directement depuis ce fichier.
        # C'est pratique pour le débogage ou l'exécution rapide.
        pytest.main([__file__])