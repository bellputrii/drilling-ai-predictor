from pydantic import BaseModel, Field


class ActivityInput(BaseModel):
    bitdepth: float = Field(..., ge=0)
    md: float = Field(..., ge=0)
    Hookload: float = Field(..., ge=0)
    mudflowin: float = Field(..., ge=0)
    rpm: float = Field(..., ge=0)
    torqa: float
    woba: float = Field(..., ge=0)
    blockpos: float = Field(..., ge=0)
    rop: float = Field(..., ge=0)
    stppress: float = Field(..., ge=0)

class CasingInput(BaseModel):
    bitdepth: float = Field(..., ge=0)
    md: float = Field(..., ge=0)
    speeddown: float = Field(..., ge=0)
    speedup: float = Field(..., ge=0)
    stppress: float = Field(..., ge=0)
    mudflowin: float = Field(..., ge=0)
    hklda: float = Field(..., ge=0)
    blockpos: float = Field(..., ge=0)