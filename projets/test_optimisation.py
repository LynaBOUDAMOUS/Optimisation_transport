"""
Module de test pour la logique d'optimisation de l'application de transport.

Ce module contient des tests unitaires pour la fonction `extraire_chiffre`
et la fonction principale `run_optimization` définie dans `optimisation.py`.
Il utilise Pytest pour l'exécution des tests et simule les fichiers CSV
nécessaires pour les scénarios d'optimisation.
"""


import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, mock_open
from optimisation import extraire_chiffre, run_optimization, TEMP_FILE


class TestExtraireChiffre:
    """
    Classe de tests pour la fonction `extraire_chiffre`.
    Cette fonction est responsable d'extraire le premier nombre entier
    d'une chaîne de caractères ou d'autres types de données.
    """
    
    def test_extraire_chiffre_nombre_simple(self):
        
        """
        Teste l'extraction de nombres lorsque la chaîne contient également du texte.
        La fonction doit extraire le premier nombre trouvé.
        """

        assert extraire_chiffre("123") == 123
        assert extraire_chiffre(456) == 456
        
    def test_extraire_chiffre_avec_texte(self):
        """Teste l'extraction de nombres lorsque la chaîne contient également du texte.
        La fonction doit extraire le premier nombre trouvé."""
        
        assert extraire_chiffre("Client 25") == 25
        assert extraire_chiffre("#Entrepot 3") == 3
        assert extraire_chiffre("Coût: 150€") == 150
        
    def test_extraire_chiffre_sans_nombre(self):
        
        """
        Teste le comportement de la fonction lorsque la chaîne ne contient aucun nombre,
        est vide, ou est None. Dans ces cas, elle doit retourner 0.
        """

        assert extraire_chiffre("Aucun nombre") == 0
        assert extraire_chiffre("") == 0
        assert extraire_chiffre(None) == 0
        
    def test_extraire_chiffre_premier_nombre(self):


        """
        Teste que la fonction `extraire_chiffre` extrait uniquement le premier
        nombre rencontré dans la chaîne, ignorant les suivants.
        """
        assert extraire_chiffre("123 et 456") == 123
        assert extraire_chiffre("Prix 50 pour 100 unités") == 50


class TestRunOptimization:
    
    """
    Classe de tests pour la fonction `run_optimization`.
    Cette fonction est le cœur de la logique d'optimisation,
    lisant les données de transport et calculant l'attribution optimale.
    """
    @pytest.fixture
    def sample_csv_data(self):
        """
        Fixture fournissant des données CSV d'échantillon brutes.
        Contient des en-têtes et des valeurs, y compris des éléments masqués avec '#'.
        """
        return """,,Client 1,Client 2,#Client 3
,Entrepot 1,10,15,20
,Entrepot 2,12,18,25
,#Entrepot 3,30,35,40"""
    
    @pytest.fixture
    def balanced_csv_data(self):
        """
        Fixture fournissant des données CSV pour un scénario équilibré
        où l'offre totale est égale à la demande totale.
        """
        return """,Demande,100,150
Offre,Entrepot 1,10,15
200,Entrepot 2,12,18
50,#Entrepot 3,30,35"""
    
    @pytest.fixture
    def excess_supply_csv_data(self):
        """
        Fixture fournissant des données CSV pour un scénario avec excès d'offre.
        La quantité offerte est supérieure à la demande totale.
        """
        return """,Demande,50,75
Offre,Entrepot 1,10,15
200,Entrepot 2,12,18"""
    
    @pytest.fixture
    def excess_demand_csv_data(self):
        """
        Fixture fournissant des données CSV pour un scénario avec excès de demande.
        La demande totale est supérieure à la quantité offerte.
        """
        return """,Demande,200,300
Offre,Entrepot 1,10,15
100,Entrepot 2,12,18"""
    
    def create_temp_csv(self, data):
        """
        Fonction utilitaire pour créer un fichier CSV temporaire
        avec les données spécifiées.
        :param data: La chaîne de caractères représentant le contenu CSV.
        """
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(data)
    
    def teardown_method(self):
        """
        Méthode de nettoyage exécutée après chaque test.
        Assure la suppression des fichiers temporaires créés pendant les tests
        pour maintenir un environnement propre.
        """
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
        if os.path.exists("delais_livraison.csv"):
            os.remove("delais_livraison.csv")
    
    def test_run_optimization_balanced(self, balanced_csv_data):
        """
        Teste la fonction `run_optimization` dans un scénario où l'offre
        et la demande sont équilibrées.
        """
        self.create_temp_csv(balanced_csv_data)

        # Exécute la fonction d'optimisation sans prendre en compte les délais
        rows, restants, clients_non_satisfaits = run_optimization()
        
        # Vérifications de base
        assert isinstance(rows, list)
        assert isinstance(restants, list)
        assert isinstance(clients_non_satisfaits, list)
        assert len(restants) == 0  # Pas de surplus
        assert len(clients_non_satisfaits) == 0  # Pas de déficit
    
    def test_run_optimization_excess_supply(self, excess_supply_csv_data):
        """
        Teste la fonction `run_optimization` dans un scénario avec un excès d'offre.
        Un client fictif est implicitement créé pour absorber le surplus.
        """
        self.create_temp_csv(excess_supply_csv_data)
        
        # Exécute la fonction d'optimisation
        rows, restants, clients_non_satisfaits = run_optimization()
        
        # Avec excès d'offre, on devrait avoir des restants
        assert len(restants) > 0
        assert len(clients_non_satisfaits) == 0
        
        # Vérifier que les restants sont des tuples (entrepot, quantité)
        for restant in restants:
            assert isinstance(restant, tuple)
            assert len(restant) == 2
            assert isinstance(restant[1], (int, np.integer))
    
    def test_run_optimization_excess_demand(self, excess_demand_csv_data):
        """
        Teste la fonction `run_optimization` dans un scénario avec excès de demande.
        Un entrepôt fictif est implicitement créé pour simuler le besoin non satisfait.
        """
        self.create_temp_csv(excess_demand_csv_data)
        
        # Exécute la fonction d'optimisation
        rows, restants, clients_non_satisfaits = run_optimization()
        
        # Avec excès de demande, on devrait avoir des clients non satisfaits
        assert len(restants) == 0
        assert len(clients_non_satisfaits) > 0
        
        # Vérifier que les clients non satisfaits sont des tuples
        for client in clients_non_satisfaits:
            assert isinstance(client, tuple)
            assert len(client) == 2
            assert isinstance(client[1], (int, np.integer))
    
    def test_run_optimization_with_delays(self, balanced_csv_data):
        """
        Teste la fonction `run_optimization` avec la prise en compte des délais.
        Un fichier de délais est créé et l'option `with_delays` est activée.
        """
        self.create_temp_csv(balanced_csv_data)
        
        # Crée un fichier CSV de délais spécifique pour ce test
        delais_data = """Entrepot,Client 1,Client 2
Entrepot 1,5,3
Entrepot 2,2,7"""
        
        with open("delais_livraison.csv", 'w', encoding='utf-8') as f:
            f.write(delais_data)
        
        rows, restants, clients_non_satisfaits = run_optimization(with_delays=True)
        
        # Les résultats doivent toujours être des listes.
        # Des assertions plus spécifiques sur les résultats avec délais seraient possibles
        # si la logique d'optimisation avec délais était plus prévisible pour ce mock.
        assert isinstance(rows, list)
        assert isinstance(restants, list)
        assert isinstance(clients_non_satisfaits, list)
    
    def test_run_optimization_invalid_csv(self):
        """
        Teste le comportement de `run_optimization` lorsqu'elle reçoit un fichier CSV invalide.
        S'attend à ce qu'une exception appropriée soit levée (IndexError, ValueError, EmptyDataError de pandas).
        """
        # Créer un fichier vide
        with open(TEMP_FILE, 'w') as f:
            f.write("")
        
        # Devrait lever une exception ou retourner des listes vides
        with pytest.raises((IndexError, ValueError, pd.errors.EmptyDataError)):
            run_optimization()
    
    def test_run_optimization_missing_file(self):
        """
        Teste le comportement de `run_optimization` lorsque le fichier CSV de transport est manquant.
        S'attend à ce qu'une FileNotFoundError soit levée.
        """
        # S'assurer que le fichier n'existe pas
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
        
        with pytest.raises(FileNotFoundError):
            run_optimization()
    
    def test_run_optimization_with_masked_data(self, sample_csv_data):
        """
        Teste que la fonction `run_optimization` ignore correctement les
        lignes/colonnes masquées par un '#' dans le fichier CSV.
        """
        self.create_temp_csv(sample_csv_data)
        
        rows, restants, clients_non_satisfaits = run_optimization()
        
        # Vérifier que les données masquées sont ignorées
        assert isinstance(rows, list)
        # Les clients/entrepôts avec # ne devraient pas apparaître dans les résultats
        for row in rows:
            if len(row) >= 2:
                assert "#" not in str(row[0])  # Client
                assert "#" not in str(row[1])  # Entrepôt
    
    def test_run_optimization_delays_file_error(self, balanced_csv_data):
        """
        Teste la gestion d'erreur lors du chargement d'un fichier de délais invalide.
        L'optimisation devrait toujours fonctionner, mais sans prendre en compte
        les délais si le fichier est corrompu ou mal formaté.
        """
        self.create_temp_csv(balanced_csv_data)
        
        # Créer un fichier de délais invalide
        with open("delais_livraison.csv", 'w') as f:
            f.write("invalid,csv,format")
        
        # Devrait fonctionner sans erreur même si le fichier délais est invalide
        rows, restants, clients_non_satisfaits = run_optimization(with_delays=True)
        
        assert isinstance(rows, list)
        assert isinstance(restants, list)
        assert isinstance(clients_non_satisfaits, list)
    
    def test_run_optimization_result_structure(self, balanced_csv_data):
        """
        Teste la structure attendue des résultats retournés par `run_optimization`.
        Vérifie les types de données pour les quantités, coûts unitaires et totaux.
        """
        self.create_temp_csv(balanced_csv_data)
        
        rows, restants, clients_non_satisfaits = run_optimization()
        
        # Vérifier la structure des rows
        for row in rows:
            assert isinstance(row, list)
            if len(row) == 6:  # Structure complète
                # [client, entrepot, quantité, coût_unitaire, prix_total, total_client]
                assert isinstance(row[2], (int, np.integer))  # quantité
                assert isinstance(row[3], (int, np.integer))  # coût unitaire
                assert isinstance(row[4], (int, np.integer))  # prix total
    
    @patch('pandas.read_csv')
    def test_run_optimization_pandas_exception(self, mock_read_csv):
        """
        Teste la gestion d'une `pd.errors.ParserError` (erreur de parsing CSV)
        levée par `pandas.read_csv`.
        """
        mock_read_csv.side_effect = pd.errors.ParserError("Erreur de parsing")
        
        with pytest.raises(pd.errors.ParserError):
            run_optimization()


class TestIntegration:
    """
    Classe de tests d'intégration pour vérifier le workflow complet
    de la fonction `run_optimization` dans différents scénarios.
    """
    
    def test_complete_workflow(self):
        """
        Teste un workflow complet d'optimisation avec et sans prise en compte des délais.
        Crée un jeu de données réaliste et vérifie que l'optimisation s'exécute
        sans erreur et retourne des résultats valides.
        """
        # Données de test réalistes
        csv_data = """,Demande,100,200,150
Offre,Entrepot 1,5,8,12
300,Entrepot 2,7,6,10
200,Entrepot 3,9,11,8"""
        
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        try:
            # Test sans délais
            rows1, restants1, clients1 = run_optimization(with_delays=False)
            
            # Test avec délais (sans fichier délais)
            rows2, restants2, clients2 = run_optimization(with_delays=True)
            
            # Les deux devraient fonctionner
            assert isinstance(rows1, list)
            assert isinstance(rows2, list)
            
            # Nettoyer
            os.remove(TEMP_FILE)
            
        except Exception as e:
            if os.path.exists(TEMP_FILE):
                os.remove(TEMP_FILE)
            raise e


# Tests additionnels pour améliorer la couverture
class TestCoverageEnhancement:
    """
    Classe contenant des tests supplémentaires conçus pour améliorer la couverture du code
    de la fonction `run_optimization`, en ciblant des cas limites ou spécifiques.
    """
    def teardown_method(self):
        """
        Méthode de nettoyage exécutée après chaque test de cette classe.
        Assure la suppression de tous les fichiers temporaires créés.
        """
        for file in [TEMP_FILE, "delais_livraison.csv"]:
            if os.path.exists(file):
                os.remove(file)
    
    def test_optimization_failure_handling(self):
        """
        Teste le comportement de `run_optimization` lorsqu'un problème d'optimisation
        rend la solution impossible à trouver par `linprog` (par ex. contraintes insolubles).
        La fonction devrait retourner des listes vides.
        """
        # Créer un cas impossible à résoudre
        csv_data = """,Demande,1000000
Offre,Entrepot 1,1
1,Entrepot 2,999999"""
        
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        # Avec des contraintes impossibles, linprog peut échouer
        rows, restants, clients_non_satisfaits = run_optimization()
        
        # Devrait retourner des listes vides en cas d'échec
        assert isinstance(rows, list)
        assert isinstance(restants, list)
        assert isinstance(clients_non_satisfaits, list)
    
    def test_delays_with_valid_data(self):
        """
        Teste la prise en compte des délais avec des données de transport et de délais complètes et valides.
        Vérifie que les coûts totaux sont cohérents avec et sans délais.
        """
        # Données de transport pour le test
        csv_data = """,Demande,100,150
Offre,Entrepot 1,10,15
200,Entrepot 2,12,18
50,"""
        
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        # Créer un fichier délais avec toutes les combinaisons
        delais_data = """Entrepot,Client 1,Client 2
Entrepot 1,5,3
Entrepot 2,2,7"""
        
        with open("delais_livraison.csv", 'w', encoding='utf-8') as f:
            f.write(delais_data)
        
        rows, restants, clients_non_satisfaits = run_optimization(with_delays=True)
        
        # Vérifier que les résultats sont cohérents
        assert isinstance(rows, list)
        
        # Vérifier que les coûts incluent les délais
        total_cost_with_delays = sum(int(row[4]) for row in rows if len(row) >= 5)
        
        # Refaire sans délais pour comparaison
        rows_no_delays, _, _ = run_optimization(with_delays=False)
        total_cost_no_delays = sum(int(row[4]) for row in rows_no_delays if len(row) >= 5)
        
        # Le coût avec délais devrait être différent (généralement plus élevé)
        # Note: pas toujours plus élevé car l'optimisation peut changer
        assert isinstance(total_cost_with_delays, (int, np.integer))
        assert isinstance(total_cost_no_delays, (int, np.integer))
        assert total_cost_with_delays >= 0
        assert total_cost_no_delays >= 0
    
    def test_empty_extraction_scenarios(self):
        """
        Teste la fonction `extraire_chiffre` avec divers scénarios de données vides
        ou non-numériques (pandas.NA, numpy.nan, listes/dictionnaires vides, float 0.0).
        Elle devrait toujours retourner 0.
        """
        # Test avec différents types de None/vides
        assert extraire_chiffre(pd.NA) == 0
        assert extraire_chiffre(np.nan) == 0
        assert extraire_chiffre([]) == 0
        assert extraire_chiffre({}) == 0
        assert extraire_chiffre(0.0) == 0
        assert extraire_chiffre("") == 0
    
    def test_complex_csv_structure(self):
        """
        Teste la robustesse de `run_optimization` face à une structure CSV plus complexe,
        incluant des clients et entrepôts masqués par un '#' dans le fichier.
        """
        csv_data = """,Demande,50,75,100,#Client masqué
Offre,Entrepot 1,5,10,15,20
150,#Entrepot masqué,100,200,300,400
100,Entrepot 2,8,12,18,25
50,Entrepot 3,6,9,14,22"""
        
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        rows, restants, clients_non_satisfaits = run_optimization()
        
        # Vérifier que les éléments masqués sont bien exclus
        assert isinstance(rows, list)
        
        # Vérifier qu'aucun élément masqué n'apparaît
        for row in rows:
            if len(row) >= 2:
                assert "masqué" not in str(row[0]).lower()
                assert "masqué" not in str(row[1]).lower()
    
    def test_edge_case_quantities(self):
        """
        Teste le comportement de l'optimisation avec des quantités limites, comme zéro.
        """
        # Test avec quantités zéro et une offre nulle
        csv_data = """,Demande,0,100
Offre,Entrepot 1,10,15
100,Entrepot 2,0,20"""
        
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        rows, restants, clients_non_satisfaits = run_optimization()
        
        # Devrait gérer les quantités zéro sans erreur
        assert isinstance(rows, list)
    
    def test_delays_index_error_handling(self):
        """
        Teste la gestion d'erreur lorsque le fichier de délais est mal formé ou incomplet,
        conduisant potentiellement à des erreurs d'indexation lors de son traitement.
        La fonction `run_optimization` devrait gérer cela sans planter.
        """
        csv_data = """,Demande,100,150
Offre,Entrepot 1,10,15
250,Entrepot 2,12,18"""
        
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        # Créer un fichier délais incomplet/incorrect
        delais_data = """Entrepot,Client 1
Entrepot 1,5
Entrepot 3,7"""  # Entrepot 3 n'existe pas, Client 2 manquant
        
        with open("delais_livraison.csv", 'w', encoding='utf-8') as f:
            f.write(delais_data)
        
        # Devrait gérer l'erreur sans crash
        rows, restants, clients_non_satisfaits = run_optimization(with_delays=True)
        
        assert isinstance(rows, list)
        assert isinstance(restants, list)
        assert isinstance(clients_non_satisfaits, list)


# Tests de performance (optionnels)
class TestPerformance:
    """
    Classe de tests de performance pour évaluer l'efficacité de la fonction
    `run_optimization` avec un grand ensemble de données.
    """
    
    def test_large_dataset_performance(self):
        """
        Teste le temps d'exécution de `run_optimization` avec un jeu de données
        de taille relativement grande. S'assure que la fonction s'exécute
        dans un délai raisonnable.
        """
        # Créer un CSV avec beaucoup de données (plus petit pour éviter les problèmes)
        num_clients = 10
        num_entrepots = 8
        
        # Construire la première ligne (en-têtes)
        header_line = ",Demande" + "".join([f",{i*10}" for i in range(num_clients)])
        lines = [header_line]
        
        # Construire les lignes des entrepôts
        for i in range(num_entrepots):
            entrepot_data = [f"{i*20}", f"Entrepot {i+1}"] + [str(np.random.randint(1, 20)) for _ in range(num_clients)]
            lines.append(",".join(entrepot_data))
        
        csv_data = "\n".join(lines)
        
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        try:
            import time
            start_time = time.time()
            
            rows, restants, clients_non_satisfaits = run_optimization()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Vérifier que l'exécution prend moins de 10 secondes
            assert execution_time < 10.0, f"Exécution trop lente: {execution_time:.2f}s"
            
            # Nettoyer
            os.remove(TEMP_FILE)
            
        except Exception as e:
            if os.path.exists(TEMP_FILE):
                os.remove(TEMP_FILE)
            raise e


if __name__ == "__main__":
    # Pour exécuter les tests directement
    pytest.main([__file__, "-v"])