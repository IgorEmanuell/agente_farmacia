#!/usr/bin/env python3
# populate_db.py
import asyncio
from loguru import logger

# Adjust import path if necessary, assuming running from project root
from src.database import AsyncSessionFactory, add_product, init_db

async def populate():
    logger.info("Initializing DB for population...")
    await init_db() # Ensure tables exist

    logger.info("Populating database with example products...")
    async with AsyncSessionFactory() as session:
        products_to_add = [
            {"nome": "Dipirona Gotas 20ml", "categoria": "Analgésico", "preco": 8.50, "estoque": 50, "exige_receita": False},
            {"nome": "Paracetamol 750mg 20 Comprimidos", "categoria": "Analgésico", "preco": 12.00, "estoque": 35, "exige_receita": False},
            {"nome": "Amoxicilina 500mg 21 Cápsulas", "categoria": "Antibiótico", "preco": 25.90, "estoque": 15, "exige_receita": True},
            {"nome": "Loratadina 10mg 12 Comprimidos", "categoria": "Antialérgico", "preco": 15.75, "estoque": 40, "exige_receita": False},
            {"nome": "Omeprazol 20mg 28 Cápsulas", "categoria": "Gástrico", "preco": 18.00, "estoque": 0, "exige_receita": False}, # Out of stock example
            {"nome": "Rivotril 2mg 30 Comprimidos", "categoria": "Controlado", "preco": 35.50, "estoque": 10, "exige_receita": True}, # Requires recipe
            {"nome": "Vitamina C Efervescente 10 Tubos", "categoria": "Vitamina", "preco": 22.00, "estoque": 100, "exige_receita": False},
        ]

        added_count = 0
        for prod_data in products_to_add:
            try:
                # Simple check if product already exists (by name) - could be more robust
                # Import locally to avoid circular dependency issues if models import database stuff
                from sqlalchemy.future import select
                from src.models import Produto
                stmt = select(Produto).where(Produto.nome == prod_data["nome"])
                result = await session.execute(stmt)
                existing = result.scalars().first()
                
                if not existing:
                    # Use the existing add_product function which handles commit
                    await add_product(session, prod_data)
                    added_count += 1
                else:
                    # Corrected logger info to be single line and properly indented
                    logger.info(f"Product '{prod_data['nome']}' already exists, skipping.") # Single line logger
            except Exception as e:
                # Corrected indentation and logging
                logger.error(f"Error adding product {prod_data.get('nome', 'N/A')}: {e}")
                # Rollback is implicitly handled by session context manager if add_product fails
                # Continue with the next product

        logger.info(f"Finished populating database. Added {added_count} new products.")

if __name__ == "__main__":
    asyncio.run(populate())

