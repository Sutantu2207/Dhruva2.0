#!/usr/bin/env python3
"""Dhruva.AI V2 — Database Seeder CLI.

Run this script to initialize all database tables and seed foundational data:
    python backend/seed.py

Or target a specific remote database:
    DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname python backend/seed.py
"""

import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.persistence.postgres.database import engine, AsyncSessionFactory
from src.infrastructure.seed import init_schema, seed_all_data
from src.core.config import get_settings


async def main():
    settings = get_settings()
    print("=" * 70)
    print("Dhruva.AI V2 — Database Initializer & Seeder")
    print(f"Target Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print("=" * 70)

    print("\n[1/2] Verifying schema and creating tables...")
    await init_schema(engine)

    print("\n[2/2] Seeding foundational institutional data, roles, users & course...")
    async with AsyncSessionFactory() as session:
        result = await seed_all_data(session)

    print("\n" + "=" * 70)
    print("SUCCESS: Database fully seeded!")
    print("=" * 70)
    print("\nDefault Seeded Accounts (Password for all: SecurePass123!):")
    print(" - Super Admin:        superadmin@dhruva.ai")
    print(" - Institution Admin:  admin@iitb.ac.in")
    print(" - HOD (CSE):          hod.cse@iitb.ac.in")
    print(" - Faculty:            prof.verma@iitb.ac.in")
    print(" - Student:            rahul.k@iitb.ac.in")
    print(" - Placement Officer:  placement@iitb.ac.in")
    print(f"\nInstitution Slug:      {result.get('institution', 'iit-bombay')}")
    print("Primary Course:        CS101 (Data Structures and Algorithms)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
