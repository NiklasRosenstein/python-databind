
"""
Provides the #precision() annotation which can be used to control the #decimal.Context for
de/serialization of decimal values.
"""

import decimal
import typing as t
from dataclasses import dataclass
from databind.core.annotations.base import Annotation


@dataclass
class precision(Annotation):
  prec: t.Optional[int] = None
  rounding: t.Optional[str] = None
  Emin: t.Optional[int] = None
  Emax: t.Optional[int] = None
  capitals: t.Optional[bool] = None
  clamp: t.Optional[bool] = None

  def to_context(self) -> decimal.Context:
    return decimal.Context(
      prec=self.prec, rounding=self.rounding, Emin=self.Emin, Emax=self.Emax,
      capitals=self.capitals, clamp=self.clamp)
