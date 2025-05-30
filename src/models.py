# src/models.py
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
import datetime

Base = declarative_base()

# --- SQLAlchemy Models --- #

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True, nullable=False)
    categoria = Column(String, index=True)
    preco = Column(Float)
    estoque = Column(Integer, default=0)
    exige_receita = Column(Boolean, default=False)
    timestamp_criacao = Column(DateTime(timezone=True), server_default=func.now())
    timestamp_atualizacao = Column(DateTime(timezone=True), onupdate=func.now())

    reservas = relationship("Reserva", back_populates="produto")

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    cliente_jid = Column(String, index=True, nullable=False) # JID from WhatsApp
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pendente") # e.g., pendente, confirmada, cancelada, retirada

    produto = relationship("Produto", back_populates="reservas")

# --- Pydantic Models (for API validation/serialization) --- #

class ProdutoBase(BaseModel):
    nome: str
    categoria: Optional[str] = None
    preco: Optional[float] = None
    estoque: Optional[int] = 0
    exige_receita: Optional[bool] = False

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoRead(ProdutoBase):
    id: int
    timestamp_criacao: datetime.datetime
    timestamp_atualizacao: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True # Compatibility with SQLAlchemy models

class ReservaBase(BaseModel):
    cliente_jid: str
    produto_id: int
    quantidade: int
    status: Optional[str] = "pendente"

class ReservaCreate(ReservaBase):
    pass

class ReservaRead(ReservaBase):
    id: int
    timestamp: datetime.datetime
    produto: Optional[ProdutoRead] = None # Include product details if needed

    class Config:
        orm_mode = True

