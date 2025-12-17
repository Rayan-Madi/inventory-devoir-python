"""
cli.py — Interface console (menu interactif)

Pourquoi ce fichier ?
- C’est la couche “présentation” : inputs utilisateur, affichage, navigation menu.
- Elle doit rester simple : pas de SQL direct ici, pas de calcul métier complexe ici.

Ce qui est déjà fait (starter) :
- Menu interactif complet (8 options)
- Option 1 : Initialisation JSON → SQLite (fonctionnelle)
- Option 2 : Afficher inventaire (fonctionnelle)
- Les options 3 à 7 sont des TODO guidés

Ce que vous devez faire :
- Implémenter progressivement les options 3..7 en appelant `InventoryManager`.
"""

from __future__ import annotations

import argparse
import logging

from .config import AppConfig
from .exceptions import (
    DataImportError,
    DatabaseError,
    InventoryError,
    ValidationError,
)
from .logging_conf import configure_logging
from .services import InventoryManager
from .utils import format_table

logger = logging.getLogger(__name__)


def _prompt(text: str) -> str:
    return input(text).strip()


def print_menu() -> None:
    print("\n=== Gestion de stock (JSON → SQLite) ===")
    print("1) Initialiser le stock (depuis un JSON)")
    print("2) Afficher l’inventaire")
    print("3) Ajouter un produit   (TODO)")
    print("4) Modifier un produit  (TODO)")
    print("5) Supprimer un produit (TODO)")
    print("6) Vendre un produit    (TODO)")
    print("7) Tableau de bord      (TODO)")
    print("8) Quitter")


def render_inventory_table(products) -> str:
    headers = ["ID", "SKU", "Nom", "Catégorie", "Prix HT", "TVA", "Prix TTC", "Stock"]
    rows = []
    for p in products:
        unit_ttc = round(p.unit_price_ht * (1 + p.vat_rate), 2)
        rows.append([
            str(p.id or ""),
            p.sku,
            p.name,
            p.category,
            f"{p.unit_price_ht:.2f}",
            f"{p.vat_rate:.2f}",
            f"{unit_ttc:.2f}",
            str(p.quantity),
        ])
    return format_table(headers, rows)


def action_initialize(app: InventoryManager) -> None:
    default_path = "data/initial_stock.json"
    path = _prompt(f"Chemin du JSON d'initialisation [{default_path}] : ")
    path = path or default_path
    count = app.initialize_from_json(path, reset=True)
    print(f"Initialisation réussie : {count} produit(s) importé(s).")


def action_list_inventory(app: InventoryManager) -> None:
    products = app.list_inventory()
    if not products:
        print("(inventaire vide)")
        return
    print("\n" + render_inventory_table(products))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Inventory CLI — starter kit")
    p.add_argument("--db", default="data/inventory.db", help="Chemin du fichier SQLite (.db)")
    p.add_argument("--log-level", default="INFO", help="DEBUG/INFO/WARNING/ERROR")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    configure_logging(log_level=args.log_level)
    config = AppConfig(db_path=args.db)
    app = InventoryManager(config)

    logger.info("App started with db=%s", config.db_path)

    while True:
        try:
            print_menu()
            choice = _prompt("Votre choix (1-8) : ")

            if choice == "1":
                action_initialize(app)
            elif choice == "2":
                action_list_inventory(app)
            elif choice in {"3", "4", "5", "6", "7"}:
                print("Fonctionnalité TODO : à implémenter par l'étudiant selon l'énoncé.")
            elif choice == "8":
                print("Au revoir.")
                return 0
            else:
                print("Choix invalide. Veuillez saisir un nombre entre 1 et 8.")

        except (ValidationError, DataImportError) as e:
            logger.warning("Validation/import error: %s", e)
            print(f"Erreur: {e}")
        except DatabaseError as e:
            logger.error("Database error: %s", e)
            print(f"Erreur base de données: {e}")
        except InventoryError as e:
            logger.error("Inventory error: %s", e)
            print(f"Erreur: {e}")
        except KeyboardInterrupt:
            print("\nInterruption utilisateur. Au revoir.")
            return 130
        except Exception:
            logger.exception("Unexpected error")
            print("Erreur inattendue. Consultez le fichier de logs.")
            return 1
