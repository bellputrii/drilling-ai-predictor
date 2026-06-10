from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.sql import func

from database.connection import Base


class ActivityPrediction(Base):
    __tablename__ = "activity_predictions"

    id = Column(Integer, primary_key=True, index=True)

    bitdepth = Column(Float, nullable=False)
    md = Column(Float, nullable=False)
    Hookload = Column(Float, nullable=False)
    mudflowin = Column(Float, nullable=False)
    rpm = Column(Float, nullable=False)
    torqa = Column(Float, nullable=False)
    woba = Column(Float, nullable=False)
    blockpos = Column(Float, nullable=False)
    rop = Column(Float, nullable=False)
    stppress = Column(Float, nullable=False)

    prediction_code = Column(Integer, nullable=False)
    prediction_label = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    confidence_level = Column(String(20), nullable=False)

    probabilities = Column(JSON, nullable=True)
    rule_signals = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=
    func.now())

class CasingPrediction(Base):
    __tablename__ = "casing_predictions"

    id = Column(Integer, primary_key=True, index=True)

    bitdepth = Column(Float, nullable=False)
    md = Column(Float, nullable=False)
    speeddown = Column(Float, nullable=False)
    speedup = Column(Float, nullable=False)
    stppress = Column(Float, nullable=False)
    mudflowin = Column(Float, nullable=False)
    hklda = Column(Float, nullable=False)
    blockpos = Column(Float, nullable=False)

    prediction_code = Column(Integer, nullable=False)
    prediction_label = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    confidence_level = Column(String(20), nullable=False)

    probabilities = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())