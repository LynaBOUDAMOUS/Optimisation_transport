"""
Service pour la gestion des délais de livraison.
Contient la logique métier séparée de l'interface utilisateur.
"""
import pandas as pd
import os
from typing import List, Tuple, Optional


class DelaisService:
    """Service pour gérer les délais de livraison."""
    
    def __init__(self, fichier_delais: str = "delais_livraison.csv"):
        """
        Initialise le service avec le fichier des délais.
        
        Args:
            fichier_delais: Chemin vers le fichier CSV des délais
        """
        self.fichier_delais = fichier_delais
        self._delais_df = None
    
    def fichier_existe(self) -> bool:
        """Vérifie si le fichier des délais existe."""
        return os.path.exists(self.fichier_delais)
    
    def charger_delais(self) -> pd.DataFrame:
        """
        Charge les délais depuis le fichier CSV.
        
        Returns:
            DataFrame contenant les délais
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            pd.errors.EmptyDataError: Si le fichier est vide
        """
        if not self.fichier_existe():
            raise FileNotFoundError(f"Fichier {self.fichier_delais} introuvable.")
        
        try:
            self._delais_df = pd.read_csv(self.fichier_delais)
            return self._delais_df.copy()
        except pd.errors.EmptyDataError:
            raise pd.errors.EmptyDataError(f"Le fichier {self.fichier_delais} est vide.")
    
    def obtenir_clients(self) -> List[str]:
        """
        Retourne la liste des clients (colonnes sauf 'Entrepot').
        
        Returns:
            Liste des noms de clients
        """
        if self._delais_df is None:
            self.charger_delais()
        return list(self._delais_df.columns[1:])
    
    def obtenir_entrepots(self) -> List[str]:
        """
        Retourne la liste des entrepôts (lignes sauf 'Max_Delai_Client').
        
        Returns:
            Liste des noms d'entrepôts
        """
        if self._delais_df is None:
            self.charger_delais()
        return [e for e in self._delais_df["Entrepot"].tolist() 
                if e != "Max_Delai_Client"]
    
    def obtenir_delai(self, entrepot: str, client: str) -> Optional[int]:
        """
        Obtient le délai entre un entrepôt et un client.
        
        Args:
            entrepot: Nom de l'entrepôt
            client: Nom du client
            
        Returns:
            Délai en jours ou None si non trouvé
        """
        if self._delais_df is None:
            self.charger_delais()
        
        try:
            mask = self._delais_df["Entrepot"] == entrepot
            if not mask.any():
                return None
            
            if client not in self._delais_df.columns:
                return None
                
            return int(self._delais_df.loc[mask, client].values[0])
        except (IndexError, ValueError):
            return None
    
    def modifier_delai(self, entrepot: str, client: str, nouveau_delai: int) -> bool:
        """
        Modifie le délai entre un entrepôt et un client.
        
        Args:
            entrepot: Nom de l'entrepôt
            client: Nom du client
            nouveau_delai: Nouveau délai en jours
            
        Returns:
            True si la modification a réussi, False sinon
            
        Raises:
            ValueError: Si le délai est négatif
        """
        if nouveau_delai < 0:
            raise ValueError("Le délai doit être positif.")
        
        if self._delais_df is None:
            self.charger_delais()
        
        # Vérification de l'existence de l'entrepôt et du client
        if entrepot not in self.obtenir_entrepots():
            return False
        
        if client not in self.obtenir_clients():
            return False
        
        # Modification du délai
        mask = self._delais_df["Entrepot"] == entrepot
        self._delais_df.loc[mask, client] = nouveau_delai
        
        return True
    
    def obtenir_delai_max_client(self, client: str) -> Optional[int]:
        """
        Obtient le délai maximum accepté par un client.
        
        Args:
            client: Nom du client
            
        Returns:
            Délai maximum en jours ou None si non trouvé
        """
        if self._delais_df is None:
            self.charger_delais()
        
        try:
            mask = self._delais_df["Entrepot"] == "Max_Delai_Client"
            if not mask.any():
                return None
            
            if client not in self._delais_df.columns:
                return None
                
            return int(self._delais_df.loc[mask, client].values[0])
        except (IndexError, ValueError):
            return None
    
    def modifier_delai_max_client(self, client: str, nouveau_delai_max: int) -> bool:
        """
        Modifie le délai maximum accepté par un client.
        
        Args:
            client: Nom du client
            nouveau_delai_max: Nouveau délai maximum en jours
            
        Returns:
            True si la modification a réussi, False sinon
            
        Raises:
            ValueError: Si le délai est négatif
        """
        if nouveau_delai_max < 0:
            raise ValueError("Le délai doit être positif.")
        
        if self._delais_df is None:
            self.charger_delais()
        
        # Vérification de l'existence du client et de la ligne Max_Delai_Client
        if client not in self.obtenir_clients():
            return False
        
        mask = self._delais_df["Entrepot"] == "Max_Delai_Client"
        if not mask.any():
            return False
        
        # Modification du délai maximum
        self._delais_df.loc[mask, client] = nouveau_delai_max
        
        return True
    
    def sauvegarder(self) -> bool:
        """
        Sauvegarde les délais dans le fichier CSV.
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        if self._delais_df is None:
            return False
        
        try:
            self._delais_df.to_csv(self.fichier_delais, index=False)
            return True
        except Exception:
            return False
    
    def valider_entrepot_client(self, entrepot: str, client: str) -> Tuple[bool, str]:
        """
        Valide qu'un entrepôt et un client existent.
        
        Args:
            entrepot: Nom de l'entrepôt
            client: Nom du client
            
        Returns:
            Tuple (valide, message_erreur)
        """
        if entrepot not in self.obtenir_entrepots():
            return False, f"L'entrepôt '{entrepot}' n'existe pas."
        
        if client not in self.obtenir_clients():
            return False, f"Le client '{client}' n'existe pas."
        
        return True, ""
    
    def valider_client(self, client: str) -> Tuple[bool, str]:
        """
        Valide qu'un client existe.
        
        Args:
            client: Nom du client
            
        Returns:
            Tuple (valide, message_erreur)
        """
        if client not in self.obtenir_clients():
            return False, f"Le client '{client}' n'existe pas."
        
        return True, ""