
import mypy.plugin
from ._mypy_dataclasses import DataclassTransformer as _DataclassTransformer

class DatabindPlugin(mypy.plugin.Plugin):

  def get_class_decorator_hook(self, fullname: str):
    if fullname == 'databind.core._datamodel.datamodel':
      def hook(ctx: mypy.plugin.ClassDefContext) -> None:
        _DataclassTransformer(ctx).transform()
      return hook
    return None
