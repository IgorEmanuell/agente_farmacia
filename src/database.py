# src/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from loguru import logger
import yaml
import os

# Import Base from the models file
from .models import Base, Produto, Reserva # Import models as well for potential direct use/type hinting

# Load configuration
try:
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error("Configuration file config/config.yaml not found for database setup.")
    config = {}
except yaml.YAMLError as e:
    logger.error(f"Error parsing configuration file for database setup: {e}")
    config = {}

DATABASE_URL = config.get("database", {}).get("url", "sqlite+aiosqlite:///./data/farmacia.db")

logger.info(f"Database URL: {DATABASE_URL}")

# Ensure the database directory exists (especially for SQLite)
if DATABASE_URL.startswith("sqlite"):
    db_path = DATABASE_URL.split("///")[-1]
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"Created database directory: {db_dir}")

engine = create_async_engine(DATABASE_URL, echo=False) # Set echo=True for SQL logging
AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Initializes the database and creates tables if they don't exist."""
    async with engine.begin() as conn:
        logger.info("Initializing database and creating tables if they don't exist...")
        # Create tables based on models defined in models.py that inherit from Base
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables checked/created.")

async def get_db_session() -> AsyncSession:
    """Dependency injector to get a database session for FastAPI routes."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            # Committing is usually handled within the route/function using the session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

# --- CRUD Operations --- #

# Product Operations
async def get_product_by_name(db: AsyncSession, name: str) -> Produto | None:
    """Fetches a product by its name (case-insensitive partial match)."""
    # Using ilike for case-insensitive matching and % for partial matching
    stmt = select(Produto).where(Produto.nome.ilike(f"%{name}%"))
    result = await db.execute(stmt)
    product = result.scalars().first()
    if product:
        # Corrected: Strictly single line logger info
        logger.info(f"Found product matching '{name}': '{product.nome}'")
    else:
        # Corrected: Strictly single line logger info
        logger.info(f"No product found matching '{name}'")
    return product

async def add_product(db: AsyncSession, product_data: dict) -> Produto:
    """Adds a new product to the database."""
    new_product = Produto(**product_data)
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    logger.info(f"Added new product: {new_product.nome}") # Already single line
    return new_product

# Reservation Operations
async def create_reservation(db: AsyncSession, reservation_data: dict) -> Reserva:
    """Creates a new reservation in the database."""
    # Ensure product exists and has stock before creating reservation (logic might be better in agent_logic)
    product_id = reservation_data.get("produto_id")
    quantity = reservation_data.get("quantidade", 1)

    product = await db.get(Produto, product_id)
    if not product:
        logger.error(f"Cannot create reservation. Product ID {product_id} not found.") # Already single line
        raise ValueError(f"Product ID {product_id} not found.")

    if product.estoque < quantity:
        # Corrected: Strictly single line logger warning
        logger.warning(f"Cannot reserve {quantity} of '{product.nome}'. Only {product.estoque} in stock.")
        raise ValueError(f"Insufficient stock for {product.nome}. Available: {product.estoque}")

    # Decrease stock (consider race conditions in high concurrency scenarios)
    product.estoque -= quantity
    db.add(product) # Add product back to session to update stock

    # Create reservation
    new_reservation = Reserva(**reservation_data)
    db.add(new_reservation)

    await db.commit()
    await db.refresh(new_reservation)
    await db.refresh(product) # Refresh product to get updated stock
    # Corrected: Strictly single line logger info
    logger.info(f"Created reservation {new_reservation.id} for {quantity} of '{product.nome}'. New stock: {product.estoque}")
    return new_reservation

