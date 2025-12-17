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
    print("2) Afficher l'inventaire")
    print("3) Ajouter un produit")
    print("4) Modifier un produit")
    print("5) Supprimer un produit")
    print("6) Vendre un produit")
    print("7) Tableau de bord")
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

def action_add_product(app: InventoryManager) -> None:
    """Ajouter un produit."""
    print("\n--- Ajouter un produit ---")
    sku = _prompt("SKU : ")
    name = _prompt("Nom : ")
    category = _prompt("Catégorie : ")
    
    prix_str = _prompt("Prix HT : ")
    qty_str = _prompt("Quantité : ")
    tva_str = _prompt("TVA (défaut 0.20) : ") or "0.20"
    
    try:
        prix_ht = float(prix_str)
        qty = int(qty_str)
        tva = float(tva_str)
    except ValueError:
        print("Erreur : prix/quantité/TVA invalides")
        return
    
    app.add_product(sku, name, category, prix_ht, qty, tva)
    print(f"Produit {sku} ajouté avec succès !")
def action_update_product(app: InventoryManager) -> None:
    """Modifier un produit."""
    print("\n--- Modifier un produit ---")
    sku = _prompt("SKU du produit à modifier : ")
    
    # verif existence
    products = app.list_inventory()
    if not any(p.sku == sku for p in products):
        print(f"Produit {sku} introuvable")
        return
    
    print("Laissez vide pour ne pas modifier un champ")
    name = _prompt("Nouveau nom : ") or None
    category = _prompt("Nouvelle catégorie : ") or None
    prix_str = _prompt("Nouveau prix HT : ")
    qty_str = _prompt("Nouvelle quantité : ")
    tva_str = _prompt("Nouvelle TVA : ")
    
    prix_ht = float(prix_str) if prix_str else None
    qty = int(qty_str) if qty_str else None
    tva = float(tva_str) if tva_str else None
    
    try:
        app.update_product(sku, name, category, prix_ht, qty, tva)
        print(f"Produit {sku} modifié !")
    except ValueError as e:
        print(f"Erreur : {e}")


def action_delete_product(app: InventoryManager) -> None:
    """Supprimer un produit."""
    print("\n--- Supprimer un produit ---")
    sku = _prompt("SKU du produit à supprimer : ")
    
    confirm = _prompt(f"Confirmer la suppression de {sku} ? (oui/non) : ")
    if confirm.lower() != "oui":
        print("Suppression annulée")
        return
    
    app.delete_product(sku)
    print(f"Produit {sku} supprimé !")

def action_sell_product(app: InventoryManager) -> None:
    """Vendre un produit."""
    print("\n--- Vendre un produit ---")
    sku = _prompt("SKU du produit : ")
    qty_str = _prompt("Quantité à vendre : ")
    
    try:
        qty = int(qty_str)
        result = app.sell_product(sku, qty)
        
        print(f"\n✓ Vente enregistrée !")
        print(f"  SKU: {result['sku']}")
        print(f"  Quantité: {result['quantity']}")
        print(f"  Total HT: {result['total_ht']:.2f} €")
        print(f"  TVA: {result['total_vat']:.2f} €")
        print(f"  Total TTC: {result['total_ttc']:.2f} €")
    except ValueError as e:
        print(f"Erreur : {e}")

def action_dashboard(app: InventoryManager) -> None:
    """Affiche le tableau de bord des ventes."""
    print("\n=== TABLEAU DE BORD ===")
    
    try:
        stats = app.get_dashboard()
        
        if stats["nb_ventes"] == 0:
            print("(Aucune vente enregistrée)")
            return
        
        print(f"\n📊 Statistiques globales :")
        print(f"  Nombre de ventes : {stats['nb_ventes']}")
        print(f"  Quantité totale vendue : {stats['qty_totale']}")
        print(f"\n💰 Chiffre d'affaires :")
        print(f"  CA HT        : {stats['ca_ht']:.2f} €")
        print(f"  TVA totale   : {stats['tva_totale']:.2f} €")
        print(f"  CA TTC       : {stats['ca_ttc']:.2f} €")
        
    except Exception as e:
        print(f"Erreur : {e}")

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
            elif choice == "3":
                action_add_product(app)
            elif choice == "4":
                action_update_product(app)
            elif choice == "5":
                action_delete_product(app)
            elif choice == "6":
                action_sell_product(app)
            elif choice == "7":
                action_dashboard(app)
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
