"""
Initialize database by applying SQL migrations.

Usage:
    python scripts/init_db.py

Requires:
    - DATABASE_URL environment variable
    - PostgreSQL running with pgvector extension
"""

import os
import sys
import glob
from pathlib import Path

def main():
    migrations_dir = Path(__file__).parent.parent / "database" / "migrations"

    if not migrations_dir.exists():
        print(f"ERROR: Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    sql_files = sorted(glob.glob(str(migrations_dir / "*.sql")))

    if not sql_files:
        print("No migration files found")
        sys.exit(1)

    print("=" * 50)
    print("  Database Initialization")
    print("=" * 50)
    print()
    print(f"Found {len(sql_files)} migration files:")
    for f in sql_files:
        print(f"  - {os.path.basename(f)}")

    print()
    print("To apply migrations:")
    print("  1. Local: supabase db reset")
    print("  2. Cloud: supabase db push")
    print()
    print("Or apply manually with psql:")
    print(f"  psql $DATABASE_URL -f <migration_file>")


if __name__ == "__main__":
    main()
