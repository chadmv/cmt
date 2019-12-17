from pyparsing import (
    Literal,
    Word,
    Group,
    Forward,
    alphas,
    alphanums,
    Regex,
    ParseException,
    CaselessKeyword,
    Suppress,
    delimitedList,
)
import maya.cmds as cmds
import math
import operator
from six import string_types


def dge(expression, **kwargs):
    parser = DGParser(**kwargs)
    return parser.eval(expression)


class DGParser(object):
    # map operator symbols to corresponding arithmetic operations
    epsilon = 1e-12

    def __init__(self, **kwargs):
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        self.kwargs = kwargs
        self.expr_stack = []
        self.expression_string = None
        self.results = None

        self.opn = {
            "+": self.add,
            "-": self.subtract,
            "*": self.multiply,
            "/": self.divide,
            "^": self.pow,
        }

        self.fn = {
            "exp": self.exp,
            "clamp": self.clamp,
            "cos": math.cos,
            "tan": math.tan,
            "abs": abs,
            "trunc": lambda a: int(a),
            "round": round,
            "sgn": lambda a: -1 if a < -epsilon else 1 if a > epsilon else 0,
        }

        # use CaselessKeyword for e and pi, to avoid accidentally matching
        # functions that start with 'e' or 'pi' (such as 'exp'); Keyword
        # and CaselessKeyword only match whole words
        e = CaselessKeyword("E")
        pi = CaselessKeyword("PI")
        # fnumber = Combine(Word("+-"+nums, nums) +
        #                    Optional("." + Optional(Word(nums))) +
        #                    Optional(e + Word("+-"+nums, nums)))
        # or use provided pyparsing_common.number, but convert back to str:
        # fnumber = ppc.number().addParseAction(lambda t: str(t[0]))
        fnumber = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
        ident = Word(alphas, alphanums + "_$")

        plus, minus, mult, div = map(Literal, "+-*/")
        lpar, rpar = map(Suppress, "()")
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")

        expr = Forward()
        expr_list = delimitedList(Group(expr))
        # add parse action that replaces the function identifier with a (name, number of args) tuple
        fn_call = (ident + lpar - Group(expr_list) + rpar).setParseAction(
            lambda t: t.insert(0, (t.pop(0), len(t[0])))
        )
        atom = (
            addop[...]
            + (
                (fn_call | pi | e | fnumber | ident).setParseAction(self.push_first)
                | Group(lpar + expr + rpar)
            )
        ).setParseAction(self.push_unary_minus)

        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left
        # exponents, instead of left-to-right that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor <<= atom + (expop + factor).setParseAction(self.push_first)[...]
        term = factor + (multop + factor).setParseAction(self.push_first)[...]
        expr <<= term + (addop + term).setParseAction(self.push_first)[...]
        self.bnf = expr

    def eval(self, expression_string):
        self.expression_string = expression_string
        self.expr_stack = []
        self.results = self.bnf.parseString(expression_string, True)
        return self.evaluate_stack(self.expr_stack[:])

    def push_first(self, toks):
        self.expr_stack.append(toks[0])

    def push_unary_minus(self, toks):
        for t in toks:
            if t == "-":
                self.expr_stack.append("unary -")
            else:
                break

    def evaluate_stack(self, s):
        op, num_args = s.pop(), 0
        if isinstance(op, tuple):
            op, num_args = op
        if op == "unary -":
            op1 = self.evaluate_stack(s)
            result = self.multiply(-1, op1)
            self.add_notes(result, "*", -1, op1)
            return result
        elif op in "+-*/^":
            # note: operands are pushed onto the stack in reverse order
            op2 = self.evaluate_stack(s)
            op1 = self.evaluate_stack(s)
            result = self.opn[op](op1, op2)
            self.add_notes(result, op, op1, op2)
            return result
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            # note: args are pushed onto the stack in reverse order
            args = reversed([self.evaluate_stack(s) for _ in range(num_args)])
            args = list(args)
            result = self.fn[op](*args)
            self.add_notes(result, op, *args)
            return result
        elif op[0].isalpha():
            value = self.kwargs.get(op)
            if value is None:
                raise Exception("invalid identifier '%s'" % op)
            return value
        else:
            # try to evaluate as int first, then as float if int fails
            try:
                return int(op)
            except ValueError:
                return float(op)

    def add(self, v1, v2):
        return self._connect_plus_minus_average(1, v1, v2)

    def subtract(self, v1, v2):
        return self._connect_plus_minus_average(2, v1, v2)

    def _connect_plus_minus_average(self, operation, v1, v2):
        array_types = ["double3", "float3"]
        pma = cmds.createNode("plusMinusAverage")
        cmds.setAttr("{}.operation".format(pma), operation)
        in_attr = "input1D"
        out_attr = "output1D"
        for v in [v1, v2]:
            if isinstance(v, string_types) and attribute_type(v) in array_types:
                in_attr = "input3D"
                out_attr = "output3D"

        for i, v in enumerate([v1, v2]):
            if isinstance(v, string_types):
                if attribute_type(v) in array_types:
                    cmds.connectAttr(v, "{}.{}[{}]".format(pma, in_attr, i))
                else:
                    if in_attr == "input3D":
                        for x in "xyz":
                            cmds.connectAttr(
                                v, "{}.{}[{}].input3D{}".format(pma, in_attr, i, x)
                            )
                    else:
                        cmds.connectAttr(v, "{}.{}[{}]".format(pma, in_attr, i))
            else:
                if in_attr == "input3D":
                    for x in "xyz":
                        cmds.setAttr(
                            "{}.{}[{}].input3D{}".format(pma, in_attr, i, x), v
                        )
                else:
                    cmds.setAttr("{}.{}[{}]".format(pma, in_attr, i), v)
        return "{}.{}".format(pma, out_attr)

    def multiply(self, v1, v2):
        return self._connect_multiply_divide(1, v1, v2)

    def divide(self, v1, v2):
        return self._connect_multiply_divide(2, v1, v2)

    def pow(self, v1, v2):
        return self._connect_multiply_divide(3, v1, v2)

    def exp(self, v):
        return self._connect_multiply_divide(3, math.e, v)

    def _connect_multiply_divide(self, operation, v1, v2):
        array_types = ["double3", "float3"]
        mdn = cmds.createNode("multiplyDivide")
        cmds.setAttr("{}.operation".format(mdn), operation)
        value_count = 1
        for v in [v1, v2]:
            if isinstance(v, string_types) and attribute_type(v) in array_types:
                value_count = 3

        for i, v in enumerate([v1, v2]):
            i += 1
            if isinstance(v, string_types):
                if attribute_type(v) in array_types:
                    cmds.connectAttr(v, "{}.input{}".format(mdn, i))
                else:
                    if value_count == 3:
                        for x in "XYZ":
                            cmds.connectAttr(v, "{}.input{}{}".format(mdn, i, x))
                    else:
                        cmds.connectAttr(v, "{}.input{}X".format(mdn, i))
            else:
                if value_count == 3:
                    for x in "XYZ":
                        cmds.setAttr("{}.input{}{}".format(mdn, i, x), v)
                else:
                    cmds.setAttr("{}.input{}X".format(mdn, i), v)
        return "{}.output".format(mdn) if value_count == 3 else "{}.outputX".format(mdn)

    def clamp(self, value, min_value, max_value):
        array_types = ["double3", "float3"]
        clamp = cmds.createNode("clamp")

        for v, attr in [[min_value, "min"], [max_value, "max"]]:
            if isinstance(v, string_types):
                if attribute_type(v) in array_types:
                    cmds.connectAttr(v, "{}.{}".format(clamp, attr))
                else:
                    for x in "RGB":
                        cmds.connectAttr(v, "{}.{}{}".format(clamp, attr, x))
            else:
                for x in "RGB":
                    cmds.setAttr("{}.{}{}".format(clamp, attr, x), v)

        value_count = 1
        if isinstance(value, string_types):
            if attribute_type(value) in array_types:
                value_count = 3
                cmds.connectAttr(value, "{}.input".format(clamp))
            else:
                for x in "RGB":
                    cmds.connectAttr(value, "{}.input{}".format(clamp, x))
        else:
            # Unlikely for a static value to be clamped, but it should still work
            for x in "RGB":
                cmds.setAttr("{}.input{}".format(clamp, x), value)
        return (
            "{}.output".format(clamp)
            if value_count == 3
            else "{}.outputR".format(clamp)
        )

    def add_notes(self, node, op, *args):
        node = node.split(".")[0]
        attrs = cmds.listAttr(node, ud=True) or []
        if "notes" not in attrs:
            cmds.addAttr(node, ln="notes", dt="string")
        keys = self.kwargs.keys()
        keys.sort()
        args = [str(v) for v in args]
        if op in self.fn:
            op_str = "{}({})".format(op, ", ".join(args))
        else:
            op_str = (op.join(args),)
        notes = "Node generated by dge\n\nExpression:\n  {}\n\nOperation:\n  {}\n\nkwargs:\n  {}".format(
            self.expression_string,
            op_str,
            "\n  ".join(["{}: {}".format(x, self.kwargs[x]) for x in keys]),
        )
        cmds.setAttr("{}.notes".format(node), notes, type="string")


def attribute_type(a):
    tokens = a.split(".")
    node = tokens[0]
    attribute = ".".join(tokens[1:])
    return cmds.attributeQuery(attribute, node=node, at=True)
