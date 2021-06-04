
"""
Provides the #precision() annotation which can be used to control the #decimal.Context for
de/serialization of decimal values.
"""

import decimal
import typing as t
from dataclasses import dataclass
from nr.pylang.utils import NotSet
from . import Annotation


@dataclass
class precision(Annotation):
  prec: t.Optional[int] = None
  rounding: t.Optional[int] = None
  Emin: t.Optional[int] = None
  Emax: t.Optional[int] = None
  capitals: t.Optional[bool] = None
  clamp: t.Optional[bool] = None
  flags: t.Union[None, NotSet, int] = NotSet.Value
  traps: t.Optional[int] = None

  def to_context(self) -> decimal.Context:
    flags_and_traps = {'traps': self.traps}
    if self.flags is not NotSet.Value:
      flags_and_traps['flags'] = self.flags
    return decimal.Context(
      prec=self.prec, rounding=self.rounding, Emin=self.Emin, Emax=self.Emax,
      capitals=self.capitals, clamp=self.clamp, **flags_and_traps
    )
