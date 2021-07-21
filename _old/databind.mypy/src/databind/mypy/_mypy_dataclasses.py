
"""
Code copied from #mypy.plugins.dataclasses and adapter to work with the #databind.core package.
"""

import typing as t
import mypy
from mypy.plugins.dataclasses import (
    Argument,
    AssignmentStmt,
    CallExpr,
    ClassDefContext,
    DataclassAttribute,
    Dict,
    Expression,
    Instance,
    List,
    NameExpr,
    NoneType,
    Optional,
    PlaceholderNode,
    RefExpr,
    SymbolTableNode,
    TempNode,
    Tuple,
    TypeInfo,
    TypeVarDef,
    TypeVarExpr,
    TypeVarType,
    Var,
    add_method,
    get_proper_type,
    make_wildcard_trigger,
    ARG_POS,
    MDEF,
    SELF_TVAR_NAME,
)
from mypy.plugins.dataclasses import _get_decorator_bool_argument


def no_rhs(context: t.Optional[mypy.nodes.Context] = None) -> mypy.nodes.TempNode:
    node = mypy.nodes.TempNode(mypy.types.AnyType(mypy.types.TypeOfAny.special_form), no_rhs=True)
    if context:
        node.set_line(context)
    return node


class DataclassTransformer:
    def __init__(self, ctx: ClassDefContext) -> None:
        self._ctx = ctx

    def transform(self) -> None:
        """Apply all the necessary transformations to the underlying
        dataclass so as to ensure it is fully type checked according
        to the rules in PEP 557.
        """
        ctx = self._ctx
        info = self._ctx.cls.info
        attributes = self.collect_attributes()
        if attributes is None:
            # Some definitions are not ready, defer() should be already called.
            return
        for attr in attributes:
            if attr.type is None:
                ctx.api.defer()
                return
        decorator_arguments = {
            'init': _get_decorator_bool_argument(self._ctx, 'init', True),
            'eq': _get_decorator_bool_argument(self._ctx, 'eq', True),
            'order': _get_decorator_bool_argument(self._ctx, 'order', False),
            'frozen': _get_decorator_bool_argument(self._ctx, 'frozen', False),
        }

        # If there are no attributes, it may be that the semantic analyzer has not
        # processed them yet. In order to work around this, we can simply skip generating
        # __init__ if there are no attributes, because if the user truly did not define any,
        # then the object default __init__ with an empty signature will be present anyway.
        if (decorator_arguments['init'] and
                ('__init__' not in info.names or info.names['__init__'].plugin_generated) and
                attributes):
            add_method(
                ctx,
                '__init__',
                args=[attr.to_argument() for attr in attributes if attr.is_in_init],
                return_type=NoneType(),
            )

        if (decorator_arguments['eq'] and info.get('__eq__') is None or
                decorator_arguments['order']):
            # Type variable for self types in generated methods.
            obj_type = ctx.api.named_type('__builtins__.object')
            self_tvar_expr = TypeVarExpr(SELF_TVAR_NAME, info.fullname + '.' + SELF_TVAR_NAME,
                                         [], obj_type)
            info.names[SELF_TVAR_NAME] = SymbolTableNode(MDEF, self_tvar_expr)

        # Add <, >, <=, >=, but only if the class has an eq method.
        if decorator_arguments['order']:
            if not decorator_arguments['eq']:
                ctx.api.fail('eq must be True if order is True', ctx.cls)

            for method_name in ['__lt__', '__gt__', '__le__', '__ge__']:
                # Like for __eq__ and __ne__, we want "other" to match
                # the self type.
                obj_type = ctx.api.named_type('__builtins__.object')
                order_tvar_def = TypeVarDef(SELF_TVAR_NAME, info.fullname + '.' + SELF_TVAR_NAME,
                                            -1, [], obj_type)
                order_other_type = TypeVarType(order_tvar_def)
                order_return_type = ctx.api.named_type('__builtins__.bool')
                order_args = [
                    Argument(Var('other', order_other_type), order_other_type, None, ARG_POS)
                ]

                existing_method = info.get(method_name)
                if existing_method is not None and not existing_method.plugin_generated:
                    assert existing_method.node
                    ctx.api.fail(
                        'You may not have a custom %s method when order=True' % method_name,
                        existing_method.node,
                    )

                add_method(
                    ctx,
                    method_name,
                    args=order_args,
                    return_type=order_return_type,
                    self_type=order_other_type,
                    tvar_def=order_tvar_def,
                )

        if decorator_arguments['frozen']:
            self._freeze(attributes)

        self.reset_init_only_vars(info, attributes)

        info.metadata['dataclass'] = {
            'attributes': [attr.serialize() for attr in attributes],
            'frozen': decorator_arguments['frozen'],
        }

    def reset_init_only_vars(self, info: TypeInfo, attributes: List[DataclassAttribute]) -> None:
        """Remove init-only vars from the class and reset init var declarations."""
        for attr in attributes:
            if attr.is_init_var:
                if attr.name in info.names:
                    del info.names[attr.name]
                else:
                    # Nodes of superclass InitVars not used in __init__ cannot be reached.
                    assert attr.is_init_var
                for stmt in info.defn.defs.body:
                    if isinstance(stmt, AssignmentStmt) and stmt.unanalyzed_type:
                        lvalue = stmt.lvalues[0]
                        if isinstance(lvalue, NameExpr) and lvalue.name == attr.name:
                            # Reset node so that another semantic analysis pass will
                            # recreate a symbol node for this attribute.
                            lvalue.node = None

    def collect_attributes(self) -> Optional[List[DataclassAttribute]]:
        """Collect all attributes declared in the dataclass and its parents.
        All assignments of the form
          a: SomeType
          b: SomeOtherType = ...
        are collected.
        """
        # First, collect attributes belonging to the current class.
        ctx = self._ctx
        cls = self._ctx.cls
        attrs = []  # type: List[DataclassAttribute]
        known_attrs = set()  # type: Set[str]
        for stmt in cls.defs.body:
            # Any assignment that doesn't use the new type declaration
            # syntax can be ignored out of hand.
            if not (isinstance(stmt, AssignmentStmt) and stmt.new_syntax):
                continue

            # a: int, b: str = 1, 'foo' is not supported syntax so we
            # don't have to worry about it.
            lhs = stmt.lvalues[0]
            if not isinstance(lhs, NameExpr):
                continue

            sym = cls.info.names.get(lhs.name)
            if sym is None:
                # This name is likely blocked by a star import. We don't need to defer because
                # defer() is already called by mark_incomplete().
                continue

            node = sym.node
            if isinstance(node, PlaceholderNode):
                # This node is not ready yet.
                return None
            assert isinstance(node, Var)

            # x: ClassVar[int] is ignored by dataclasses.
            if node.is_classvar:
                continue

            # x: InitVar[int] is turned into x: int and is removed from the class.
            is_init_var = False
            node_type = get_proper_type(node.type)
            if (isinstance(node_type, Instance) and
                    node_type.type.fullname == 'dataclasses.InitVar'):
                is_init_var = True
                node.type = node_type.args[0]

            has_field_call, field_args = _collect_field_args(stmt.rvalue)

            is_in_init_param = field_args.get('init')
            if is_in_init_param is None:
                is_in_init = True
            else:
                is_in_init = bool(ctx.api.parse_bool(is_in_init_param))

            has_default = False
            # Ensure that something like x: int = field() is rejected
            # after an attribute with a default.
            if has_field_call:
                has_default = 'default' in field_args or 'default_factory' in field_args

            # All other assignments are already type checked.
            elif not isinstance(stmt.rvalue, TempNode):
                has_default = True

            if not has_default:
                # Make all non-default attributes implicit because they are de-facto set
                # on self in the generated __init__(), not in the class body.
                sym.implicit = True
                stmt.rvalue = no_rhs(stmt.rvalue)

            # FORK: replace rvalue with default or default_factory
            elif 'default' in field_args:
                stmt.rvalue = field_args['default']
            elif 'default_factory' in field_args:
                stmt.rvalue = mypy.nodes.CallExpr(field_args['default_factory'], [], [], [])
                stmt.rvalue.set_line(field_args['default_factory'])

            known_attrs.add(lhs.name)
            attrs.append(DataclassAttribute(
                name=lhs.name,
                is_in_init=is_in_init,
                is_init_var=is_init_var,
                has_default=has_default,
                line=stmt.line,
                column=stmt.column,
                type=sym.type,
                info=cls.info,
            ))

        # Next, collect attributes belonging to any class in the MRO
        # as long as those attributes weren't already collected.  This
        # makes it possible to overwrite attributes in subclasses.
        # copy() because we potentially modify all_attrs below and if this code requires debugging
        # we'll have unmodified attrs laying around.
        all_attrs = attrs.copy()
        for info in cls.info.mro[1:-1]:
            if 'dataclass' not in info.metadata:
                continue

            super_attrs = []
            # Each class depends on the set of attributes in its dataclass ancestors.
            ctx.api.add_plugin_dependency(make_wildcard_trigger(info.fullname))

            for data in info.metadata['dataclass']['attributes']:
                name = data['name']  # type: str
                if name not in known_attrs:
                    attr = DataclassAttribute.deserialize(info, data, ctx.api)
                    known_attrs.add(name)
                    super_attrs.append(attr)
                elif all_attrs:
                    # How early in the attribute list an attribute appears is determined by the
                    # reverse MRO, not simply MRO.
                    # See https://docs.python.org/3/library/dataclasses.html#inheritance for
                    # details.
                    for attr in all_attrs:
                        if attr.name == name:
                            all_attrs.remove(attr)
                            super_attrs.append(attr)
                            break
            all_attrs = super_attrs + all_attrs

        # FORK: @datamodel allows non-default arguments after default arguments.
        '''
        # Ensure that arguments without a default don't follow
        # arguments that have a default.
        found_default = False
        for attr in all_attrs:
            # If we find any attribute that is_in_init but that
            # doesn't have a default after one that does have one,
            # then that's an error.
            if found_default and attr.is_in_init and not attr.has_default:
                # If the issue comes from merging different classes, report it
                # at the class definition point.
                context = (Context(line=attr.line, column=attr.column) if attr in attrs
                           else ctx.cls)
                ctx.api.fail(
                    'Attributes without a default cannot follow attributes with one',
                    context,
                )

            found_default = found_default or (attr.has_default and attr.is_in_init)
        '''

        return all_attrs

    def _freeze(self, attributes: List[DataclassAttribute]) -> None:
        """Converts all attributes to @property methods in order to
        emulate frozen classes.
        """
        info = self._ctx.cls.info
        for attr in attributes:
            sym_node = info.names.get(attr.name)
            if sym_node is not None:
                var = sym_node.node
                assert isinstance(var, Var)
                var.is_property = True
            else:
                var = attr.to_var()
                var.info = info
                var.is_property = True
                var._fullname = info.fullname + '.' + var.name
                info.names[var.name] = SymbolTableNode(MDEF, var)


def _collect_field_args(expr: Expression) -> Tuple[bool, Dict[str, Expression]]:
    """Returns a tuple where the first value represents whether or not
    the expression is a call to dataclass.field and the second is a
    dictionary of the keyword arguments that field() was called with.
    """
    if (
            isinstance(expr, CallExpr) and
            isinstance(expr.callee, RefExpr) and
            expr.callee.fullname in ('dataclasses.field', 'databind.core._datamodel.field')  # FORK: Add _datamodel.field
    ):
        # field() only takes keyword arguments.
        args = {}
        for name, arg in zip(expr.arg_names, expr.args):
            assert name is not None
            args[name] = arg
        return True, args
    return False, {}
