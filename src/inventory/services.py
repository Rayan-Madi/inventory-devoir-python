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

    # TODO (étudiant) :
    # - add_product / update_product / delete_product
    # - sell_product (transaction atomique + calculs)
    # - dashboard (totaux)
    # - export_sales_csv
