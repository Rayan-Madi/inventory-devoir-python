"""
services.py — Logique métier (use-cases)

Pourquoi ce fichier ?
- Centraliser la logique métier (et pas dans la CLI).
- Orchestrer validation + repository + calculs.
- Avoir des fonctions facilement testables.

Ce qui est déjà fait :
- Initialisation JSON → SQLite (reset DB)
- Listing inventaire

Ce que vous devez faire :
- Implémenter les autres use-cases : CRUD, vente, dashboard, export.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .config import AppConfig
from .models import Product, now_iso
from .repository import SQLiteRepository
from .utils import load_initial_json

logger = logging.getLogger(__name__)


class InventoryManager:
    """Service principal du domaine 'stock'."""

    def __init__(self, config: AppConfig, repo: Optional[SQLiteRepository] = None) -> None:
        self.config = config
        self.repo = repo or SQLiteRepository(config.db_path)

    def sell_product(self, sku: str, quantity: int) -> dict:
        """Vend un produit (transaction atomique)."""
        if quantity <= 0:
            raise ValueError("Quantité doit être > 0")
        
        result = self.repo.sell_product_transaction(sku, quantity)
        logger.info("Vente effectuée : %s", result)
        return result

    def initialize_from_json(self, json_path: str, reset: bool = True) -> int:
        """Initialise la DB depuis un JSON."""
        logger.info("Initialization requested from JSON: %s", json_path)
        payload = load_initial_json(json_path)
        products = payload["products"]

        if reset:
            self.repo.reset_and_create_schema()
        else:
            self.repo.create_schema_if_needed()

        count = 0
        for p in products:
            prod = Product(
                sku=p["sku"],
                name=p["name"],
                category=p["category"],
                unit_price_ht=p["unit_price_ht"],
                quantity=p["quantity"],
                vat_rate=p["vat_rate"],
                created_at=now_iso(),
            )
            self.repo.insert_product(prod)
            count += 1

        logger.info("Initialization OK. %d products inserted.", count)
        return count

    def list_inventory(self) -> List[Product]:
        """Retourne la liste des produits (inventaire)."""
        self.repo.create_schema_if_needed()
        return self.repo.list_products()

    def add_product(self, sku: str, name: str, category: str, 
                    unit_price_ht: float, quantity: int, vat_rate: float = 0.20) -> None:
        """Ajoute un nouveau produit."""
        # validation basique
        if unit_price_ht < 0:
            raise ValueError("Prix HT doit être >= 0")
        if quantity < 0:
            raise ValueError("Quantité doit être >= 0")
        if not (0 <= vat_rate <= 1):
            raise ValueError("TVA doit être entre 0 et 1")
        
        # verif sku unique dans la bdd
        existing = self.repo.get_product_by_sku(sku)
        if existing:
            raise ValueError(f"SKU {sku} existe déjà")
        
        prod = Product(
            sku=sku,
            name=name,
            category=category,
            unit_price_ht=unit_price_ht,
            quantity=quantity,
            vat_rate=vat_rate,
            created_at=now_iso(),
        )
        self.repo.insert_product(prod)
        logger.info("Produit ajouté : %s", sku)

    def update_product(self, sku: str, name: str | None = None,
                      category: str | None = None,
                      unit_price_ht: float | None = None,
                      quantity: int | None = None,
                      vat_rate: float | None = None) -> None:
        """Modifie un produit existant."""
        # validations
        if unit_price_ht is not None and unit_price_ht < 0:
            raise ValueError("Prix HT doit être >= 0")
        if quantity is not None and quantity < 0:
            raise ValueError("Quantité doit être >= 0")
        if vat_rate is not None and not (0 <= vat_rate <= 1):
            raise ValueError("TVA doit être entre 0 et 1")
        
        self.repo.update_product(sku, name, category, unit_price_ht, quantity, vat_rate)
        logger.info("Produit %s modifié", sku)

    def delete_product(self, sku: str) -> None:
        """Supprime un produit."""
        self.repo.delete_product(sku)
        logger.info("Produit %s supprimé", sku)

    # TODO (étudiant) :
    # - add_product / update_product / delete_product
    # - sell_product (transaction atomique + calculs)
    # - dashboard (totaux)
    # - export_sales_csv
