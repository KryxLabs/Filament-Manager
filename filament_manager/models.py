from sqlalchemy import Column, String, Float, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base


class Filament(declarative_base()):
    __tablename__ = "filaments"
    id = Column(String, primary_key=True)
    brand = Column(String)
    material = Column(String)
    color = Column(String)
    weight = Column(Float)
    date_opened = Column(Date)
    empty = Column(Boolean)
    open = Column(Boolean)
