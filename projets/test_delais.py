"""
Tests unitaires pour DelaisService.

Ce module contient une suite complète de tests pour la classe DelaisService,
qui gère les délais de livraison entre entrepôts et clients.

Les tests couvrent :
- L'initialisation du service
- Le chargement et la validation des données CSV
- Les opérations CRUD sur les délais (Create, Read, Update, Delete)
- La gestion des délais maximum par client
- La sauvegarde des modifications
- La validation des données d'entrée
- La gestion des erreurs et cas d'exception

Structure des données de test :
- 2 entrepôts : Entrepot_1, Entrepot_2
- 3 clients : Client_A, Client_B, Client_C
- 1 ligne spéciale : Max_Delai_Client (délais maximum acceptés)

Fixtures utilisées :
- csv_content : Contenu CSV de test standardisé
- temp_csv_file : Fichier CSV temporaire créé pour chaque test
- service : Instance de DelaisService initialisée avec le fichier temporaire

Usage :
    pytest test_delais_service.py -v                    # Tests détaillés
    pytest test_delais_service.py --cov=delais_service  # Avec coverage
    pytest test_delais_service.py -k "test_modifier"    # Tests spécifiques

Auteur: [Votre nom]
Date: [Date actuelle]
Version: 1.0
"""
import pytest
import pandas as pd
import os
import tempfile
from unittest.mock import patch, mock_open
from delais_logique import DelaisService


class TestDelaisService:
    """
    Suite de tests pour la classe DelaisService.
    
    Cette classe teste toutes les fonctionnalités du service de gestion des délais :
    
    Catégories de tests :
    1. Tests d'initialisation et configuration
    2. Tests de chargement et validation des fichiers
    3. Tests des opérations de lecture (obtenir_*)
    4. Tests des opérations de modification (modifier_*)
    5. Tests de sauvegarde et persistance
    6. Tests de validation et gestion d'erreurs
    7. Tests de workflows complets
    
    Chaque test est conçu pour être :
    - Isolé : utilise des fixtures pour éviter les effets de bord
    - Déterministe : produit toujours le même résultat
    - Documenté : avec des docstrings expliquant l'objectif
    - Complet : teste les cas normaux et les cas d'erreur
    """
    
    @pytest.fixture
    def csv_content(self):
        """
        Contenu CSV de test standardisé.
        
        Fournit un fichier CSV avec une structure typique contenant :
        - 2 entrepôts de distribution (Entrepot_1, Entrepot_2)
        - 3 clients (Client_A, Client_B, Client_C)
        - Des délais de livraison variés (3 à 12 jours)
        - Une ligne Max_Delai_Client avec les délais maximum acceptés (15 à 25 jours)
        
        Cette fixture garantit que tous les tests utilisent les mêmes données
        de base, assurant la cohérence et la reproductibilité.
        
        Returns:
            str: Contenu CSV formaté avec en-têtes et données de test
        """
        return """Entrepot,Client_A,Client_B,Client_C
Entrepot_1,5,7,10
Entrepot_2,3,8,12
Max_Delai_Client,15,20,25"""
    
    @pytest.fixture
    def temp_csv_file(self, csv_content):
        """
        Crée un fichier CSV temporaire pour les tests.
        
        Cette fixture crée un fichier temporaire avec le contenu CSV de test,
        permettant aux tests d'interagir avec un vrai fichier sans affecter
        le système de fichiers permanent.
        
        Le fichier est automatiquement nettoyé après chaque test grâce au
        mécanisme de teardown de pytest.
        
        Args:
            csv_content: Contenu CSV injecté par la fixture csv_content
            
        Yields:
            str: Chemin vers le fichier CSV temporaire créé
            
        Note:
            Le fichier est supprimé automatiquement après utilisation,
            même en cas d'échec du test.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        yield temp_path
        # Nettoyage automatique
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def service(self, temp_csv_file):
        """
        Service DelaisService initialisé avec un fichier temporaire.
        
        Cette fixture fournit une instance de DelaisService prête à l'emploi
        pour chaque test, configurée avec un fichier CSV temporaire contenant
        des données de test standardisées.
        
        Args:
            temp_csv_file: Chemin du fichier temporaire injecté par la fixture
            
        Returns:
            DelaisService: Instance du service configurée pour les tests
            
        Usage:
            Utilisée dans la plupart des tests pour avoir un service
            opérationnel sans configuration manuelle.
        """
        return DelaisService(temp_csv_file)
    
    def test_init(self):
        """
        Test de l'initialisation correcte du service.
        
        Vérifie que :
        - Le chemin du fichier est correctement stocké
        - Les données internes ne sont pas pré-chargées (lazy loading)
        - L'état initial est cohérent
        
        Ce test garantit que le constructeur fonctionne correctement
        sans effets de bord.
        """
        service = DelaisService("test.csv")
        assert service.fichier_delais == "test.csv"
        assert service._delais_df is None
    
    def test_init_default_file(self):
        """
        Test de l'initialisation avec le fichier par défaut.
        
        Vérifie que le service peut être créé sans paramètre et utilise
        le nom de fichier par défaut attendu par l'application.
        
        Important pour s'assurer que le comportement par défaut
        correspond aux attentes de l'application principale.
        """
        service = DelaisService()
        assert service.fichier_delais == "delais_livraison.csv"
    
    def test_fichier_existe_true(self, service):
        """Test de fichier_existe() quand le fichier existe."""
        assert service.fichier_existe() is True
    
    def test_fichier_existe_false(self):
        """Test de fichier_existe() quand le fichier n'existe pas."""
        service = DelaisService("fichier_inexistant.csv")
        assert service.fichier_existe() is False
    
    def test_charger_delais_success(self, service):
        """Test de chargement réussi des délais."""
        df = service.charger_delais()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ['Entrepot', 'Client_A', 'Client_B', 'Client_C']
        assert service._delais_df is not None
    
    def test_charger_delais_file_not_found(self):
        """Test de chargement avec fichier inexistant."""
        service = DelaisService("fichier_inexistant.csv")
        with pytest.raises(FileNotFoundError, match="Fichier fichier_inexistant.csv introuvable"):
            service.charger_delais()
    
    @patch("pandas.read_csv")
    def test_charger_delais_empty_file(self, mock_read_csv):
        """Test de chargement avec fichier vide."""
        mock_read_csv.side_effect = pd.errors.EmptyDataError("No columns to parse from file")
        service = DelaisService("test.csv")
        with patch.object(service, 'fichier_existe', return_value=True):
            with pytest.raises(pd.errors.EmptyDataError, match="Le fichier test.csv est vide"):
                service.charger_delais()
    
    def test_obtenir_clients(self, service):
        """Test d'obtention de la liste des clients."""
        clients = service.obtenir_clients()
        assert clients == ['Client_A', 'Client_B', 'Client_C']
    
    def test_obtenir_entrepots(self, service):
        """Test d'obtention de la liste des entrepôts."""
        entrepots = service.obtenir_entrepots()
        assert entrepots == ['Entrepot_1', 'Entrepot_2']
        assert 'Max_Delai_Client' not in entrepots
    
    def test_obtenir_delai_success(self, service):
        """Test d'obtention d'un délai existant."""
        delai = service.obtenir_delai('Entrepot_1', 'Client_A')
        assert delai == 5
        
        delai = service.obtenir_delai('Entrepot_2', 'Client_C')
        assert delai == 12
    
    def test_obtenir_delai_entrepot_inexistant(self, service):
        """Test d'obtention d'un délai avec entrepôt inexistant."""
        delai = service.obtenir_delai('Entrepot_Inexistant', 'Client_A')
        assert delai is None
    
    def test_obtenir_delai_client_inexistant(self, service):
        """Test d'obtention d'un délai avec client inexistant."""
        delai = service.obtenir_delai('Entrepot_1', 'Client_Inexistant')
        assert delai is None
    
    def test_modifier_delai_success(self, service):
        """Test de modification réussie d'un délai."""
        result = service.modifier_delai('Entrepot_1', 'Client_A', 6)
        assert result is True
        
        # Vérification de la modification
        delai = service.obtenir_delai('Entrepot_1', 'Client_A')
        assert delai == 6
    
    def test_modifier_delai_negatif(self, service):
        """Test de modification avec délai négatif."""
        with pytest.raises(ValueError, match="Le délai doit être positif"):
            service.modifier_delai('Entrepot_1', 'Client_A', -1)
    
    def test_modifier_delai_entrepot_inexistant(self, service):
        """Test de modification avec entrepôt inexistant."""
        result = service.modifier_delai('Entrepot_Inexistant', 'Client_A', 5)
        assert result is False
    
    def test_modifier_delai_client_inexistant(self, service):
        """Test de modification avec client inexistant."""
        result = service.modifier_delai('Entrepot_1', 'Client_Inexistant', 5)
        assert result is False
    
    def test_obtenir_delai_max_client_success(self, service):
        """Test d'obtention d'un délai max client existant."""
        delai_max = service.obtenir_delai_max_client('Client_A')
        assert delai_max == 15
        
        delai_max = service.obtenir_delai_max_client('Client_C')
        assert delai_max == 25
    
    def test_obtenir_delai_max_client_inexistant(self, service):
        """Test d'obtention d'un délai max avec client inexistant."""
        delai_max = service.obtenir_delai_max_client('Client_Inexistant')
        assert delai_max is None
    
    def test_modifier_delai_max_client_success(self, service):
        """Test de modification réussie d'un délai max client."""
        result = service.modifier_delai_max_client('Client_A', 18)
        assert result is True
        
        # Vérification de la modification
        delai_max = service.obtenir_delai_max_client('Client_A')
        assert delai_max == 18
    
    def test_modifier_delai_max_client_negatif(self, service):
        """Test de modification avec délai max négatif."""
        with pytest.raises(ValueError, match="Le délai doit être positif"):
            service.modifier_delai_max_client('Client_A', -1)
    
    def test_modifier_delai_max_client_inexistant(self, service):
        """Test de modification avec client inexistant."""
        result = service.modifier_delai_max_client('Client_Inexistant', 15)
        assert result is False
    
    def test_sauvegarder_success(self, service):
        """Test de sauvegarde réussie."""
        service.charger_delais()
        result = service.sauvegarder()
        assert result is True
        
        # Vérification que le fichier a été sauvegardé
        assert os.path.exists(service.fichier_delais)
    
    def test_sauvegarder_no_data(self, service):
        """Test de sauvegarde sans données chargées."""
        result = service.sauvegarder()
        assert result is False
    
    @patch("pandas.DataFrame.to_csv")
    def test_sauvegarder_exception(self, mock_to_csv, service):
        """Test de sauvegarde avec exception."""
        service.charger_delais()
        mock_to_csv.side_effect = Exception("Erreur de sauvegarde")
        
        result = service.sauvegarder()
        assert result is False
    
    def test_valider_entrepot_client_success(self, service):
        """Test de validation réussie entrepôt/client."""
        valide, message = service.valider_entrepot_client('Entrepot_1', 'Client_A')
        assert valide is True
        assert message == ""
    
    def test_valider_entrepot_client_entrepot_inexistant(self, service):
        """Test de validation avec entrepôt inexistant."""
        valide, message = service.valider_entrepot_client('Entrepot_Inexistant', 'Client_A')
        assert valide is False
        assert "L'entrepôt 'Entrepot_Inexistant' n'existe pas" in message
    
    def test_valider_entrepot_client_client_inexistant(self, service):
        """Test de validation avec client inexistant."""
        valide, message = service.valider_entrepot_client('Entrepot_1', 'Client_Inexistant')
        assert valide is False
        assert "Le client 'Client_Inexistant' n'existe pas" in message
    
    def test_valider_client_success(self, service):
        """Test de validation réussie d'un client."""
        valide, message = service.valider_client('Client_A')
        assert valide is True
        assert message == ""
    
    def test_valider_client_inexistant(self, service):
        """Test de validation avec client inexistant."""
        valide, message = service.valider_client('Client_Inexistant')
        assert valide is False
        assert "Le client 'Client_Inexistant' n'existe pas" in message
    
    def test_workflow_complet(self, service):
        """
        Test d'un workflow complet de modification et sauvegarde.
        
        Ce test d'intégration simule un scénario d'utilisation réel :
        1. Chargement des données initiales
        2. Modification d'un délai entrepôt-client
        3. Vérification de la modification en mémoire
        4. Modification d'un délai maximum client
        5. Vérification de la modification en mémoire
        6. Sauvegarde des modifications
        7. Rechargement pour vérifier la persistance
        
        Ce test garantit que toute la chaîne fonctionnelle
        fonctionne correctement de bout en bout.
        
        Scénario testé :
        - Délai Entrepot_1 -> Client_A : 5 → 8 jours
        - Délai max Client_B : 20 → 22 jours
        """
        # Chargement initial
        service.charger_delais()
        
        # Modification d'un délai
        assert service.modifier_delai('Entrepot_1', 'Client_A', 8) is True
        assert service.obtenir_delai('Entrepot_1', 'Client_A') == 8
        
        # Modification d'un délai max
        assert service.modifier_delai_max_client('Client_B', 22) is True
        assert service.obtenir_delai_max_client('Client_B') == 22
        
        # Sauvegarde
        assert service.sauvegarder() is True
        
        # Vérification de la persistance en rechargeant
        service_reload = DelaisService(service.fichier_delais)
        service_reload.charger_delais()
        assert service_reload.obtenir_delai('Entrepot_1', 'Client_A') == 8
        assert service_reload.obtenir_delai_max_client('Client_B') == 22


if __name__ == "__main__":
    pytest.main(["-v", __file__])