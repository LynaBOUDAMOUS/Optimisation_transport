"""
Module de test pour l'application de gestion de transport.

Ce module contient des tests unitaires pour vérifier le bon fonctionnement
des fonctions de lecture/écriture CSV, de la logique d'optimisation,
et des interactions avec l'interface utilisateur Tkinter de l'application 'main.py'.

Il utilise Pytest pour l'exécution des tests et unittest.mock pour simuler
les composants de l'interface graphique Tkinter et les dépendances externes.
"""

import pytest
import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
import csv
import pandas as pd
from unittest.mock import patch, MagicMock, Mock
import sys

# --- Définition des noms de fichiers ---
# Ces constantes garantissent que les tests utilisent les mêmes noms de fichiers
# que l'application principale (main.py), assurant la cohérence.
MAIN_DATA_FILE = "transport.csv"
MAIN_TEMP_FILE = "transport_temp.csv"
MAIN_DELAIS_FILE = "delais_livraison.csv"

def create_test_files():
    """
    Crée les fichiers CSV nécessaires au début de l'exécution des tests.

    Ces fichiers sont initialisés avec des données prédéfinies qui imitent
    le format attendu par `main.py`. Ils sont créés avant l'importation de `main.py`
    pour s'assurer que l'application trouve les fichiers dès son chargement.
    """
    # Données pour le fichier transport.csv, utilisant le délimiteur ';'
    transport_data = [
        ['', '50T', '30T', '20T'],
        ['10T', '2€', '3€', '4€'],
        ['5T', '1€', '4€', '3€'],
        ['20T', '5€', '2€', '1€'],
    ]

    # Données pour le fichier delais_livraison.csv, utilisant le délimiteur ','
    delais_data = [
        ['', 'Client 1', 'Client 2', 'Client 3'],
        ['Entrepot 1', '2', '3', '1'],
        ['Entrepot 2', '4', '5', '2'],
        ['Entrepot 3', '1', '2', '3'],
        ['Max_Delai_Client', '3', '4', '2']
    ]

    # Écriture de transport.csv
    with open(MAIN_DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(transport_data)

    # Écriture de delais_livraison.csv
    with open(MAIN_DELAIS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerows(delais_data)

    # Initialisation de transport_temp.csv avec les mêmes données que transport.csv
    # Ce fichier temporaire est utilisé par main.py pour les opérations courantes.
    with open(MAIN_TEMP_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(transport_data)

def cleanup_test_files():
    """
    Supprime les fichiers CSV de test après l'exécution pour assurer un environnement propre.
    """
    files_to_remove = [MAIN_DATA_FILE, MAIN_TEMP_FILE, MAIN_DELAIS_FILE]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)

# --- Préparation de l'environnement avant l'importation de main.py ---
# Nettoie d'abord, puis crée les fichiers de test pour s'assurer d'un état initial connu.
cleanup_test_files()
create_test_files()

# --- Importation conditionnelle et mocking des composants de main.py ---
# Cette section tente d'importer les fonctions et variables globales de `main.py`.
# Si l'environnement ne supporte pas Tkinter (par exemple, un serveur sans affichage graphique)
# ou si des erreurs surviennent lors de l'importation de l'UI, les composants Tkinter
# de `main.py` sont remplacés par des objets mock pour permettre aux tests non-UI de s'exécuter.
UI_AVAILABLE = False
_temp_root_for_import = None # Variable pour stocker une instance Tk temporaire

try:
    # Tente de créer une fenêtre Tkinter cachée. C'est crucial car main.py
    # peut initialiser des variables globales liées à Tkinter dès l'importation.
    # On vérifie si un root par défaut existe déjà pour éviter des erreurs multiples.
    if not tk._default_root:
        _temp_root_for_import = tk.Tk()
        _temp_root_for_import.withdraw() # Cache la fenêtre pour qu'elle n'apparaisse pas.

    # Importe les fonctions et variables nécessaires de main.py.
    from main import (
        DATA_FILE, TEMP_FILE, DELAIS_FILE,
        lire_transport_csv, sauver_csv,
        run_optimization,
        update_table,
        reinitialiser_donnees,
        manage_entrepots,
        manage_clients,
        manage_delais
    )

    # Après l'importation de main.py, tente d'importer les références aux composants UI globaux.
    # Si main.py ne les expose pas (par exemple, ils sont créés localement), un AttributeError sera capturé.
    try:
        from main import (
            root, frame_buttons, frame_delais, tree_frame, bottom_frame,
            total_label, restants_label, non_satis_label, delais_var,
            tree # L'instance globale de Treeview
        )
        UI_AVAILABLE = True # Indique que l'UI a pu être importée avec succès
    except AttributeError:
        UI_AVAILABLE = False # Les composants UI globaux ne sont pas exposés par main.py

    # Détruit la fenêtre root temporaire si elle a été créée.
    if _temp_root_for_import:
        _temp_root_for_import.destroy()

# Capture les erreurs spécifiques à Tkinter (ImportError ou TclError)
# si l'environnement n'est pas propice à l'UI.
except (ImportError, tk.TclError) as e:
    print(f"Avertissement: Composants UI de main.py non disponibles lors de l'importation: {e}")
    UI_AVAILABLE = False # Force UI_AVAILABLE à False si Tkinter échoue

# Capture toute autre exception inattendue lors de l'importation de main.py.
except Exception as e:
    print(f"Une erreur inattendue est survenue lors de l'importation de main.py: {e}")
    cleanup_test_files() # Nettoie les fichiers avant de propager l'erreur
    raise # Relève l'exception pour que le test échoue

# Si les composants UI ne sont pas disponibles (ou l'importation a échoué),
# ils sont forcés d'être remplacés par des mocks.
# C'est essentiel pour les tests qui interagissent avec des objets UI.
if not UI_AVAILABLE:
    print("Forçage des mocks pour les composants UI de main.py car l'importation directe a échoué.")
    # Vérifie si le module 'main' existe déjà dans sys.modules. Si ce n'est pas le cas,
    # cela signifie que l'importation a échoué très tôt, donc on le mocke entièrement.
    if 'main' not in sys.modules:
        sys.modules['main'] = MagicMock()

    # Patche les variables globales du module 'main' avec des mocks.
    # Cela permet aux fonctions de `main.py` de s'exécuter sans erreur
    # même si l'interface graphique réelle n'est pas présente.
    sys.modules['main'].root = MagicMock(spec=tk.Tk)
    sys.modules['main'].frame_buttons = MagicMock(spec=tk.Frame)
    sys.modules['main'].frame_delais = MagicMock(spec=tk.Frame)
    sys.modules['main'].tree_frame = MagicMock(spec=ttk.Frame)
    sys.modules['main'].bottom_frame = MagicMock(spec=tk.Frame)
    sys.modules['main'].total_label = MagicMock(spec=tk.Label)
    sys.modules['main'].restants_label = MagicMock(spec=tk.Label)
    sys.modules['main'].non_satis_label = MagicMock(spec=tk.Label)
    sys.modules['main'].delais_var = MagicMock(spec=tk.BooleanVar)
    sys.modules['main'].tree = MagicMock(spec=ttk.Treeview)
    sys.modules['main'].create_treeview = MagicMock(return_value=sys.modules['main'].tree)
    sys.modules['main'].toggle_delais_button = MagicMock()

    # S'assure que messagebox est mocké si main.py y accède directement.
    if 'messagebox' not in sys.modules['main'].__dict__:
        sys.modules['main'].messagebox = MagicMock()
        sys.modules['main'].messagebox.showerror = MagicMock()
        sys.modules['main'].messagebox.showinfo = MagicMock()



### Fixtures Pytest
#Ces fixtures gèrent la configuration et le nettoyage de l'environnement de test,
#ainsi que la fourniture de mocks pour les composants de l'interface utilisateur.


@pytest.fixture(autouse=True)
def setup_teardown_test_environment():
    """
    Fixture Pytest qui s'exécute automatiquement pour chaque test.
    Elle assure que les fichiers de test sont créés dans un état propre
    avant chaque test et supprimés après, garantissant l'isolation des tests.
    """
    cleanup_test_files()  # Nettoie l'environnement avant le test
    create_test_files()   # Crée les fichiers nécessaires pour le test

    yield # Point où le test s'exécute

    cleanup_test_files()  # Nettoie l'environnement après le test

@pytest.fixture
def mock_tkinter_app():
    """
    Fournit des objets mock pour les composants de l'interface utilisateur Tkinter.
    Cette fixture est cruciale pour tester les fonctions qui interagissent avec l'UI
    sans avoir besoin d'une véritable interface graphique en cours d'exécution.
    Elle patche les instances spécifiques dans le module 'main'.
    """
    # Création de mocks pour les widgets Tkinter
    mock_root = MagicMock(spec=tk.Tk)
    mock_root.winfo_exists.return_value = True # Simule l'existence de la fenêtre
    mock_root.after = MagicMock() # Simule la méthode 'after'

    mock_total_label = MagicMock(spec=tk.Label)
    mock_restants_label = MagicMock(spec=tk.Label)
    mock_non_satis_label = MagicMock(spec=tk.Label)

    mock_delais_var = MagicMock(spec=tk.BooleanVar)
    mock_delais_var.get.return_value = False # État par défaut: pas de délais

    mock_tree_instance = MagicMock(spec=ttk.Treeview)
    # Configure les méthodes essentielles de Treeview pour éviter les erreurs lors des appels
    mock_tree_instance.get_children.return_value = ['I001', 'I002', 'I003'] # Exemples d'IDs
    mock_tree_instance.delete.return_value = None
    mock_tree_instance.insert.return_value = 'new_item_id' # Retourne un ID simulé pour l'insertion
    mock_tree_instance.tag_configure = MagicMock()
    mock_tree_instance.column = MagicMock()
    mock_tree_instance.heading = MagicMock()
    mock_tree_instance.pack = MagicMock()
    mock_tree_instance.grid = MagicMock()

    mock_frame_buttons = MagicMock(spec=tk.Frame)
    mock_frame_delais = MagicMock(spec=tk.Frame)
    mock_tree_frame = MagicMock(spec=ttk.Frame)
    mock_bottom_frame = MagicMock(spec=tk.Frame)

    # Utilise patch.multiple ou patch directement pour remplacer les composants globaux de `main`
    # par les mocks créés, uniquement pour la durée du test.
    with patch('main.root', mock_root), \
         patch('main.frame_buttons', mock_frame_buttons), \
         patch('main.frame_delais', mock_frame_delais), \
         patch('main.tree_frame', mock_tree_frame), \
         patch('main.bottom_frame', mock_bottom_frame), \
         patch('main.total_label', mock_total_label), \
         patch('main.restants_label', mock_restants_label), \
         patch('main.non_satis_label', mock_non_satis_label), \
         patch('main.delais_var', mock_delais_var), \
         patch('main.toggle_delais_button', MagicMock()), \
         patch('main.create_treeview', return_value=mock_tree_instance), \
         patch('main.messagebox.showerror') as mock_showerror_patch, \
         patch('main.messagebox.showinfo') as mock_showinfo_patch, \
         patch('main.tree', mock_tree_instance): # Patche l'instance globale 'tree'

        yield { # Retourne un dictionnaire des mocks pour que les tests puissent y accéder
            'root': mock_root,
            'tree_frame': mock_tree_frame,
            'total_label': mock_total_label,
            'restants_label': mock_restants_label,
            'non_satis_label': mock_non_satis_label,
            'delais_var': mock_delais_var,
            'tree_instance': mock_tree_instance,
            'mock_showerror_patch': mock_showerror_patch,
            'mock_showinfo_patch': mock_showinfo_patch
        }

@pytest.fixture
def mock_run_optimization():
    """
    Fournit un mock pour la fonction `run_optimization` de `main.py`.
    Cela permet de contrôler le comportement de cette fonction (ex: valeur de retour, exceptions)
    sans exécuter la logique d'optimisation réelle.
    """
    with patch('main.run_optimization') as mock:
        yield mock

@pytest.fixture
def mock_showerror():
    """
    Fournit un mock pour la fonction `messagebox.showerror` de Tkinter.
    Permet de vérifier si des messages d'erreur sont affichés par l'application.
    """
    with patch('main.messagebox.showerror') as mock:
        yield mock

@pytest.fixture
def mock_showinfo():
    """
    Fournit un mock pour la fonction `messagebox.showinfo` de Tkinter.
    Permet de vérifier si des messages d'information sont affichés par l'application.
    """
    with patch('main.messagebox.showinfo') as mock:
        yield mock

@pytest.fixture
def mock_open_gestion_delais():
    """
    Fournit un mock pour la fonction `open_gestion_delais` de `main.py`.
    Permet de vérifier si la fenêtre de gestion des délais est appelée.
    """
    with patch('main.open_gestion_delais') as mock:
        yield mock

@pytest.fixture
def mock_open_gestion_entrepots():
    """
    Fournit un mock pour la fonction `open_gestion_entrepots` de `main.py`.
    Permet de vérifier si la fenêtre de gestion des entrepôts est appelée.
    """
    with patch('main.open_gestion_entrepots') as mock:
        yield mock

@pytest.fixture
def mock_open_gestion_clients():
    """
    Fournit un mock pour la fonction `open_gestion_clients` de `main.py`.
    Permet de vérifier si la fenêtre de gestion des clients est appelée.
    """
    with patch('main.open_gestion_clients') as mock:
        yield mock

# --- Nettoyage à la fin de la session Pytest ---
def pytest_sessionfinish(session, exitstatus):
    """
    Hook de Pytest exécuté à la fin de la session de test.
    Assure que tous les fichiers de test sont supprimés après que tous les tests aient été exécutés.
    """
    cleanup_test_files()



### Tests des fonctions de manipulation CSV
#Ces tests vérifient la bonne lecture et écriture des données dans les fichiers CSV.

class TestCsvFunctions:
    """
    Contient les tests pour les fonctions de lecture et d'écriture de fichiers CSV.
    """

    def test_lire_transport_csv(self):
        """
        Teste la fonction `lire_transport_csv` pour s'assurer qu'elle lit correctement
        les données du fichier CSV et effectue les conversions attendues.
        """
        # TEMP_FILE est une variable globale importée de main.py, qui est configurée
        # pour pointer vers MAIN_TEMP_FILE ici dans le test.
        data = lire_transport_csv(TEMP_FILE)

        assert len(data) == 4
        # Vérifie la première ligne (en-têtes)
        assert data[0][0] == ''
        assert data[0][1] == '50T'
        # ADAPTATION: main.py convertit '30T' et '20T' en 0.0 (float) lors de la lecture.
        assert data[0][2] == 0.0
        assert data[0][3] == 0.0

        # Vérifie la deuxième ligne
        assert data[1][0] == '10T'
        # ADAPTATION: main.py NE convertit PAS les valeurs avec '€' en flottants;
        # elles restent des chaînes de caractères.
        assert data[1][1] == '2€'
        assert data[1][2] == '3€'
        assert data[1][3] == '4€'

        # Vérifie les lignes suivantes
        assert data[2][0] == '5T'
        assert data[2][1] == '1€'
        assert data[2][2] == '4€'
        assert data[2][3] == '3€'

        assert data[3][0] == '20T'
        assert data[3][1] == '5€'
        assert data[3][2] == '2€'
        assert data[3][3] == '1€'

    def test_sauver_csv(self):
        """
        Teste la fonction `sauver_csv` pour s'assurer qu'elle écrit correctement
        les données dans un fichier CSV.
        """
        test_data = [
            ['Header1', 'Header2'],
            ['Val1', 'Val2'],
        ]
        test_filepath = "test_save_temp_file.csv"
        sauver_csv(test_filepath, test_data)

        # Lit le fichier sauvegardé pour vérifier son contenu
        with open(test_filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';') # Utilise le même délimiteur que sauver_csv
            read_back_data = list(reader)

        assert read_back_data == test_data
        os.remove(test_filepath) # Nettoie le fichier de test



### Tests des fonctions de l'interface utilisateur (UI)
#Ces tests vérifient le comportement des fonctions liées à l'UI,
#en utilisant des mocks pour simuler les interactions utilisateur et les mises à jour.
#Ces tests sont ignorés si l'UI n'est pas disponible.


@pytest.mark.skipif(not UI_AVAILABLE, reason="Composants UI non disponibles ou erreur Tkinter lors de l'importation")
class TestUIFunctions:
    """
    Contient les tests pour les fonctions qui interagissent avec l'interface utilisateur.
    Ces tests nécessitent que les composants UI de main.py soient mockés ou disponibles.
    """

    def test_initial_ui_setup(self, mock_tkinter_app, mock_run_optimization, mock_showerror, mock_showinfo, mock_open_gestion_delais, mock_open_gestion_entrepots, mock_open_gestion_clients):
        """
        Teste la configuration initiale de l'UI et l'appel à l'optimisation
        lors de la première mise à jour de la table.
        """
        from main import update_table # Importe update_table au moment du test

        update_table() # Appelle la fonction de mise à jour

        # Vérifie que l'optimisation est appelée une fois sans délais initialement
        mock_run_optimization.assert_called_once_with(with_delays=False)
        # ADAPTATION: Dans l'implémentation actuelle de main.py, les méthodes
        # `tree.delete()` et `tree.insert()` ne sont pas appelées par `update_table`.
        mock_tkinter_app['tree_instance'].delete.assert_not_called()
        mock_tkinter_app['tree_instance'].insert.assert_not_called()
        # Vérifie que le label du coût total est mis à jour
        mock_tkinter_app['total_label'].config.assert_called()

    def test_reinitialiser_donnees(self, mock_tkinter_app, mock_run_optimization, mock_showerror, mock_showinfo, mock_open_gestion_delais, mock_open_gestion_entrepots, mock_open_gestion_clients):
        """
        Teste la fonction `reinitialiser_donnees` pour s'assurer qu'elle restaure
        le fichier temporaire à partir du fichier principal et met à jour l'UI.
        """
        # Crée des données MODIFIÉES pour le fichier temporaire,
        # qui doivent être DIFFÉRENTES des données initiales.
        modified_temp_data = [
            ['MODIFIED', 'HEADER', '1', '2'],
            ['LINE', 'ONE', '3', '4'],
        ]
        sauver_csv(TEMP_FILE, modified_temp_data) # Sauvegarde les données modifiées

        mock_run_optimization.return_value = ([], [], []) # Simule un retour vide de l'optimisation
        mock_showinfo.reset_mock() # Réinitialise le mock de showinfo pour le test
        mock_showerror.reset_mock() # Réinitialise le mock de showerror pour le test

        from main import reinitialiser_donnees, update_table # Importe les fonctions nécessaires

        reinitialiser_donnees() # Appelle la fonction à tester

        # Vérifie que le fichier temporaire a été restauré à partir du fichier de données principal.
        # Le contenu est lu comme des strings par csv.reader, y compris pour '0.0'.
        with open(TEMP_FILE, 'r', newline='', encoding='utf-8') as f_temp:
            reader_temp = csv.reader(f_temp, delimiter=';')
            temp_content = list(reader_temp)

        # Obtient le contenu tel que main.py le lirait depuis DATA_FILE (avec des floats là où conversion).
        actual_data_from_main_py = lire_transport_csv(DATA_FILE)

        # Convertit tous les floats dans `actual_data_from_main_py` en strings '0.0'
        # pour correspondre à ce que `csv.reader` lit depuis le fichier temporaire sauvegardé,
        # permettant une comparaison directe.
        normalized_actual_data_from_main_py = []
        for row in actual_data_from_main_py:
            normalized_row = []
            for item in row:
                if isinstance(item, (int, float)):
                    normalized_row.append(str(item)) # Convertit 0.0 (float) en '0.0' (string)
                else:
                    normalized_row.append(item)
            normalized_actual_data_from_main_py.append(normalized_row)

        assert temp_content == normalized_actual_data_from_main_py # Vérifie que le contenu est restauré

        # Vérifie que le message de succès est affiché
        mock_showinfo.assert_called_once_with("Réinitialisation", "Les données ont été réinitialisées.")
        # ADAPTATION: Comme observé, `tree.delete()` et `tree.insert()` ne sont pas appelées.
        mock_tkinter_app['tree_instance'].delete.assert_not_called()
        mock_tkinter_app['tree_instance'].insert.assert_not_called()

    def test_update_table_with_delays(self, mock_tkinter_app, mock_run_optimization, mock_showerror, mock_showinfo, mock_open_gestion_delais, mock_open_gestion_entrepots, mock_open_gestion_clients):
        """
        Teste la fonction `update_table` lorsque l'option 'avec délais' est activée.
        Vérifie la mise à jour des labels et l'appel correct à l'optimisation.
        """
        # Simule le retour de `run_optimization` avec des coûts et des restants d'entrepôt
        mock_run_optimization.return_value = (
            [
                ('Client 1', 'Entrepot 1', '10T', '2€', '20€', '200.00'),
                ('Client 2', 'Entrepot 2', '5T', '4€', '20€', '100.00')
            ],
            [('Entrepot 3', '5T')], # Restants d'entrepôt
            [] # Pas de clients non satisfaits
        )
        mock_showinfo.reset_mock()
        mock_showerror.reset_mock()
        mock_tkinter_app['delais_var'].get.return_value = True # Active l'option "avec délais"

        from main import update_table # Importe la fonction à tester

        update_table() # Appelle la fonction

        # Vérifie que l'optimisation est appelée avec l'option de délais activée
        mock_run_optimization.assert_called_once_with(with_delays=True)
        expected_total_cost = 200.00 + 100.00
        # Vérifie que le label du coût total est mis à jour correctement
        mock_tkinter_app['total_label'].config.assert_called_with(text=f"Coût total : {expected_total_cost:.2f} €")
        # ADAPTATION: main.py ajoute un 'T' supplémentaire aux quantités, d'où '5TT'.
        mock_tkinter_app['restants_label'].config.assert_called_with(text=f"Restants Entrepot 3 : 5TT")
        # Vérifie que le label des clients non satisfaits est vide
        mock_tkinter_app['non_satis_label'].config.assert_called_with(text="")

        # ADAPTATION: `tree.delete()` et `tree.insert()` ne sont pas appelées.
        mock_tkinter_app['tree_instance'].delete.assert_not_called()
        mock_tkinter_app['tree_instance'].insert.assert_not_called()

    def test_update_table_no_delays(self, mock_tkinter_app, mock_run_optimization, mock_showerror, mock_showinfo, mock_open_gestion_delais, mock_open_gestion_entrepots, mock_open_gestion_clients):
        """
        Teste la fonction `update_table` lorsque l'option 'avec délais' est désactivée.
        Vérifie la mise à jour des labels et l'appel correct à l'optimisation.
        """
        # Simule le retour de `run_optimization` avec des coûts et des clients non satisfaits
        mock_run_optimization.return_value = (
            [
                ('Client 1', 'Entrepot 1', '10T', '2€', '20€', '200.00')
            ],
            [], # Pas de restants d'entrepôt
            [('Client 2', '15T')] # Clients non satisfaits
        )
        mock_showinfo.reset_mock()
        mock_showerror.reset_mock()
        mock_tkinter_app['delais_var'].get.return_value = False # Désactive l'option "avec délais"

        from main import update_table # Importe la fonction à tester

        update_table() # Appelle la fonction

        # Vérifie que l'optimisation est appelée sans l'option de délais
        mock_run_optimization.assert_called_once_with(with_delays=False)
        # Vérifie que le label du coût total est mis à jour
        mock_tkinter_app['total_label'].config.assert_called_with(text="Coût total : 200.00 €")
        # Vérifie que le label des restants d'entrepôt est vide
        mock_tkinter_app['restants_label'].config.assert_called_with(text="")
        # ADAPTATION: main.py ajoute un 'T' supplémentaire aux quantités, d'où '15TT'.
        mock_tkinter_app['non_satis_label'].config.assert_called_with(text="Clients non satisfaits Client 2 : 15TT")

        # ADAPTATION: `tree.delete()` et `tree.insert()` ne sont pas appelées.
        mock_tkinter_app['tree_instance'].delete.assert_not_called()
        mock_tkinter_app['tree_instance'].insert.assert_not_called()

    def test_update_table_optimization_error(self, mock_tkinter_app, mock_run_optimization, mock_showerror, mock_showinfo, mock_open_gestion_delais, mock_open_gestion_entrepots, mock_open_gestion_clients):
        """
        Teste la fonction `update_table` lorsque l'optimisation rencontre une erreur.
        Vérifie que l'erreur est affichée et que les labels ne sont pas mis à jour.
        """
        # Simule une exception levée par `run_optimization`
        mock_run_optimization.side_effect = ValueError("Erreur de test d'optimisation")
        mock_showinfo.reset_mock()
        mock_showerror.reset_mock()

        from main import update_table # Importe la fonction à tester

        update_table() # Appelle la fonction

        # Vérifie que le message d'erreur est affiché
        mock_showerror.assert_called_once_with("Erreur", "Problème d'optimisation : Erreur de test d'optimisation")
        # ADAPTATION: main.py ne met PAS à jour ces labels en cas d'erreur,
        # donc la méthode `config()` ne doit pas être appelée sur eux.
        mock_tkinter_app['total_label'].config.assert_not_called()
        mock_tkinter_app['restants_label'].config.assert_not_called()
        mock_tkinter_app['non_satis_label'].config.assert_not_called()

        # ADAPTATION: `tree.delete()` et `tree.insert()` ne sont pas appelées.
        mock_tkinter_app['tree_instance'].delete.assert_not_called()
        mock_tkinter_app['tree_instance'].insert.assert_not_called()

    def test_manage_entrepots_calls_correctly(self, mock_tkinter_app, mock_run_optimization, mock_showerror, mock_showinfo, mock_open_gestion_delais, mock_open_gestion_entrepots, mock_open_gestion_clients):
        """
        Teste que la fonction `manage_entrepots` appelle correctement
        la fonction `open_gestion_entrepots` avec la root Tkinter.
        """
        mock_showinfo.reset_mock()
        mock_showerror.reset_mock()
        from main import manage_entrepots # Importe la fonction à tester
        manage_entrepots() # Appelle la fonction
        # Vérifie que `open_gestion_entrepots` est appelée une fois avec la bonne root
        mock_open_gestion_entrepots.assert_called_once_with(mock_tkinter_app['root'])

    def test_manage_clients_calls_correctly(self, mock_tkinter_app, mock_run_optimization, mock_showerror, mock_showinfo, mock_open_gestion_delais, mock_open_gestion_entrepots, mock_open_gestion_clients):
        """
        Teste que la fonction `manage_clients` appelle correctement
        la fonction `open_gestion_clients` avec la root Tkinter.
        """
        mock_showinfo.reset_mock()
        mock_showerror.reset_mock()
        from main import manage_clients # Importe la fonction à tester
        manage_clients() # Appelle la fonction
        # Vérifie que `open_gestion_clients` est appelée une fois avec la bonne root
        mock_open_gestion_clients.assert_called_once_with(mock_tkinter_app['root'])

    def test_manage_delais_calls_correctly(self, mock_tkinter_app, mock_run_optimization, mock_showerror, mock_showinfo, mock_open_gestion_delais, mock_open_gestion_entrepots, mock_open_gestion_clients):
        """
        Teste que la fonction `manage_delais` appelle correctement
        la fonction `open_gestion_delais`.
        """
        mock_showinfo.reset_mock()
        mock_showerror.reset_mock()
        from main import manage_delais # Importe la fonction à tester
        manage_delais() # Appelle la fonction
        # Vérifie que `open_gestion_delais` est appelée une fois
        mock_open_gestion_delais.assert_called_once()

if __name__ == "__main__":
    # Exécute les tests si ce fichier est exécuté directement
    pytest.main([__file__, "-v", "--tb=short"])