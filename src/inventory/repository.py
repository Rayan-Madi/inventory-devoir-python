"""
repository.py — Accès aux données SQLite (DAO / Repository)

Pourquoi ce fichier ?
- Séparer la logique DB de la logique métier (services).
- Avoir une couche unique responsable des requêtes SQL.
- Faciliter tests (en remplaçant le repository si besoin).

Ce qui est déjà fait dans le starter :
- Schéma SQLite (tables products + sales)
- Reset DB + création tables
- Insertion produit
- Liste produits (inventaire)

Ce que vous devez faire :
- Ajouter les méthodes CRUD complètes.
- Ajouter la transaction atomique de vente (INSERT sale + UPDATE stock).
- Ajouter des requêtes dashboard + export ventes.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from typing import Iterable, List

from .exceptions import DatabaseError
from .models import Product, now_iso

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  unit_price_ht REAL NOT NULL CHECK(unit_price_ht >= 0),
  vat_rate REAL NOT NULL DEFAULT 0.20 CHECK(vat_rate >= 0 AND vat_rate <= 1),
  quantity INTEGER NOT NULL CHECK(quantity >= 0),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  sku TEXT NOT NULL,
  quantity INTEGER NOT NULL CHECK(quantity > 0),
  unit_price_ht REAL NOT NULL CHECK(unit_price_ht >= 0),
  vat_rate REAL NOT NULL CHECK(vat_rate >= 0 AND vat_rate <= 1),
  total_ht REAL NOT NULL CHECK(total_ht >= 0),
  total_vat REAL NOT NULL CHECK(total_vat >= 0),
  total_ttc REAL NOT NULL CHECK(total_ttc >= 0),
  sold_at TEXT NOT NULL,
  FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_sales_sku ON sales(sku);
"""


class SQLiteRepository:
    """Repository SQLite minimal (starter)."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @contextmanager
    def connect(self) -> Iterable[sqlite3.Connection]:
        """Connexion SQLite avec FK activées."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Erreur SQLite: {e}") from e
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass

    def reset_and_create_schema(self) -> None:
        """Supprime les tables puis recrée le schéma (remise à zéro)."""
        with self.connect() as conn:
            try:
                conn.execute("DROP TABLE IF EXISTS sales")
                conn.execute("DROP TABLE IF EXISTS products")
                conn.executescript(SCHEMA_SQL)
                conn.commit()
                logger.info("DB reset + schema created.")
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Erreur création schéma: {e}") from e

    def create_schema_if_needed(self) -> None:
        """Crée le schéma si les tables n'existent pas (sans reset)."""
        with self.connect() as conn:
            try:
                conn.executescript(SCHEMA_SQL)
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Erreur création schéma: {e}") from e

    def insert_product(self, p: Product) -> int:
        with self.connect() as conn:
            try:
                cur = conn.execute(
                    """
                    INSERT INTO products(sku,name,category,unit_price_ht,vat_rate,quantity,created_at)
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (p.sku, p.name, p.category, p.unit_price_ht, p.vat_rate, p.quantity, p.created_at or now_iso()),
                )
                conn.commit()
                return int(cur.lastrowid)
            except sqlite3.IntegrityError as e:
                conn.rollback()
                raise DatabaseError(f"Contrainte violée (SKU unique ?) : {e}") from e
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Erreur insert produit: {e}") from e

    def list_products(self) -> List[Product]:
        with self.connect() as conn:
            cur = conn.execute("SELECT * FROM products ORDER BY sku ASC")
            out: List[Product] = []
            for row in cur.fetchall():
                out.append(Product(
                    id=int(row["id"]),
                    sku=str(row["sku"]),
                    name=str(row["name"]),
                    category=str(row["category"]),
                    unit_price_ht=float(row["unit_price_ht"]),
                    vat_rate=float(row["vat_rate"]),
                    quantity=int(row["quantity"]),
                    created_at=str(row["created_at"]),
                ))
            return out
        
def get_product_by_sku(self, sku: str) -> Product | None:
        """Récupère un produit par son SKU (ou None si absent)."""
        with self.connect() as conn:
            cur = conn.execute("SELECT * FROM products WHERE sku = ?", (sku,))
            row = cur.fetchone()
            if not row:
                return None
            return Product(
                id=int(row["id"]),
                sku=str(row["sku"]),
                name=str(row["name"]),
                category=str(row["category"]),
                unit_price_ht=float(row["unit_price_ht"]),
                vat_rate=float(row["vat_rate"]),
                quantity=int(row["quantity"]),
                created_at=str(row["created_at"]),
            )

def get_product_by_id(self, product_id: int) -> Product | None:
        """Récupère un produit par son ID."""
        with self.connect() as conn:
            cur = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Product(
                id=int(row["id"]),
                sku=str(row["sku"]),
                name=str(row["name"]),
                category=str(row["category"]),
                unit_price_ht=float(row["unit_price_ht"]),
                vat_rate=float(row["vat_rate"]),
                quantity=int(row["quantity"]),
                created_at=str(row["created_at"]),
            )

    # TODO (étudiant) : CRUD complet, vente atomique, dashboard, export ventes
