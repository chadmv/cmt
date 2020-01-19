"""Allows the creation of node networks through equation strings.

Dependency Graph Expressions (dge) is a convenience API used to simplify the creation
of Maya DG node networks.  Rather than scripting out many createNode, get/setAttr,
connectAttr commands, you can specify a string equation.

No compiled plug-ins are used.  All created nodes are vanilla Maya nodes.  Each created
node has notes added to it to describe its place in the equation

Example Usage
=============

::

    from cmt.dge import dge

    # Create a simple mathematical graph
    loc = cmds.spaceLocator()[0]
    result = dge("(x+3)*(2+x)", x="{}.tx".format(loc))
    cmds.connectAttr(result, "{}.ty".format(loc))

    # Use assignment operator to auto-connect
    loc = cmds.spaceLocator()[0]
    dge("y=x^2", x="{}.tx".format(loc), y="{}.ty".format(loc))

    # More complex example with ternary operator and functions
    soft_ik_percentage = dge(
        "x > (1.0 - softIk)"
        "? (1.0 - softIk) + softIk * (1.0 - exp(-(x - (1.0 - softIk)) / softIk)) "
        ": x",
        x="{}.outputX".format(stretch_scale_mdn)
        softIk="{}.softIk".format(ik_control),
    )

    # Put the created nodes in a container
    soft_ik_percentage = dge(
        "x > (1.0 - softIk)"
        "? (1.0 - softIk) + softIk * (1.0 - exp(-(x - (1.0 - softIk)) / softIk)) "
        ": x",
        container="softik_equation",
        x="{}.outputX".format(stretch_scale_mdn)
        softIk="{}.softIk".format(ik_control),
    )

Supported Syntax
===================

Operators::

    +  # addition
    -  # subtraction
    *  # multiplication
    /  # division
    ^  # power,
    ?: # ternary

Functions::

    abs(x)
    exp(x)
    clamp(x, min, max)
    lerp(a, b, t)
    min(x, y)
    max(x, y)
    sqrt(x)
    cos(x)
    sin(x)
    tan(x)
    acos(x)
    asin(x)
    atan(x)
    distance(node1, node2)

Constants::

    PI
    E

Use Case
========

Before::

    # (1.0 - softik)
    one_minus = cmds.createNode(
        "plusMinusAverage", name="{}_one_minus_softik".format(self.name)
    )
    cmds.setAttr("{}.operation".format(one_minus), 2)
    cmds.setAttr("{}.input1D[0]".format(one_minus), 1)
    cmds.connectAttr(softik, "{}.input1D[1]".format(one_minus))

    # x - (1.0 - softik)
    x_minus = cmds.createNode(
        "plusMinusAverage", name="{}_x_minus_one_minus_softik".format(self.name)
    )
    cmds.setAttr("{}.operation".format(x_minus), 2)
    cmds.connectAttr(self.percent_rest_distance, "{}.input1D[0]".format(x_minus))
    cmds.connectAttr(
        "{}.output1D".format(one_minus), "{}.input1D[1]".format(x_minus)
    )

    # -(x - (1.0 - softik))
    negate = cmds.createNode(
        "multDoubleLinear", name="{}_softik_negate".format(self.name)
    )
    cmds.setAttr("{}.input1".format(negate), -1)
    cmds.connectAttr("{}.output1D".format(x_minus), "{}.input2".format(negate))

    # -(x - (1.0 - softik)) / softik
    divide = cmds.createNode(
        "multiplyDivide", name="{}_softik_divide".format(self.name)
    )
    cmds.setAttr("{}.operation".format(divide), 2)  # divide
    cmds.connectAttr("{}.output".format(negate), "{}.input1X".format(divide))
    cmds.connectAttr(softik, "{}.input2X".format(divide))

    # exp(-(x - (1.0 - softIk)) / softIk)
    exp = cmds.createNode("multiplyDivide", name="{}_softik_exp".format(self.name))
    cmds.setAttr("{}.operation".format(exp), 3)  # pow
    cmds.setAttr("{}.input1X".format(exp), 2.71828)
    cmds.connectAttr("{}.outputX".format(divide), "{}.input2X".format(exp))

    # 1.0 - exp(-(x - (1.0 - softIk)) / softIk)
    one_minus_exp = cmds.createNode(
        "plusMinusAverage", name="{}_one_minus_exp".format(self.name)
    )
    cmds.setAttr("{}.operation".format(one_minus_exp), 2)
    cmds.setAttr("{}.input1D[0]".format(one_minus_exp), 1)
    cmds.connectAttr(
        "{}.outputX".format(exp), "{}.input1D[1]".format(one_minus_exp)
    )

    # softik * (1.0 - exp(-(x - (1.0 - softIk)) / softIk))
    mdl = cmds.createNode(
        "multDoubleLinear", name="{}_softik_mdl".format(self.name)
    )
    cmds.connectAttr(softik, "{}.input1".format(mdl))
    cmds.connectAttr("{}.output1D".format(one_minus_exp), "{}.input2".format(mdl))

    # (1.0 - softik) + softik * (1.0 - exp(-(x - (1.0 - softIk)) / softIk))
    adl = cmds.createNode("addDoubleLinear", name="{}_softik_adl".format(self.name))
    cmds.connectAttr("{}.output1D".format(one_minus), "{}.input1".format(adl))
    cmds.connectAttr("{}.output".format(mdl), "{}.input2".format(adl))
    # Now output of adl is the % of the rest distance the ik handle should be from
    # the start joint

    # Only adjust the ik handle if it is less than the soft percentage threshold
    cnd = cmds.createNode(
        "condition",
        name="{}_current_length_greater_than_soft_length".format(self.name),
    )
    cmds.setAttr("{}.operation".format(cnd), 2)  # greater than
    cmds.connectAttr(self.percent_rest_distance, "{}.firstTerm".format(cnd))
    cmds.connectAttr("{}.output1D".format(one_minus), "{}.secondTerm".format(cnd))
    cmds.connectAttr("{}.output".format(adl), "{}.colorIfTrueR".format(cnd))
    cmds.connectAttr(self.percent_rest_distance, "{}.colorIfFalseR".format(cnd))

    softik_percentage = "{}.outColorR".format(cnd)


After::

    soft_ik_percentage = dge(
        "x > (1.0 - softIk)"
        "? (1.0 - softIk) + softIk * (1.0 - exp(-(x - (1.0 - softIk)) / softIk)) "
        ": x",
        container="{}_softik".format(self.name),
        x=self.percent_rest_distance,
        softIk=softik,
    )

"""
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
    oneOf,
    infixNotation,
    opAssoc,
    ParseResults,
    Optional,
    FollowedBy,
)
import maya.cmds as cmds
import math
import operator
from six import string_types

_parser = None


def dge(expression, container=None, **kwargs):
    global _parser
    if _parser is None:
        _parser = DGParser()
    return _parser.eval(expression, container=container, **kwargs)


class DGParser(object):
    def __init__(self):
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
        self.kwargs = {}
        self.expr_stack = []
        self.assignment_stack = []
        self.expression_string = None
        self.results = None
        self.container = None
        # Look up to optimize redundant nodes
        self.created_nodes = {}

        self.opn = {
            "+": self.add,
            "-": self.subtract,
            "*": self.multiply,
            "/": self.divide,
            "^": self.pow,
        }

        self.fn = {
            "abs": self.abs,
            "exp": self.exp,
            "clamp": self.clamp,
            "lerp": self.lerp,
            "min": self.min,
            "max": self.max,
            "sqrt": self.sqrt,
            "cos": self.cos,
            "sin": self.sin,
            "tan": self.tan,
            "acos": self.acos,
            "asin": self.asin,
            "atan": self.atan,
            "distance": self.distance,
        }
        self.conditionals = ["==", "!=", ">", ">=", "<", "<="]

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
        comparison_op = oneOf(" ".join(self.conditionals))
        qm, colon = map(Literal, "?:")
        assignment = Literal("=")
        assignment_op = ident + assignment + ~FollowedBy(assignment)

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
        comparison = expr + (comparison_op + expr).setParseAction(self.push_first)[...]
        ternary = (
            comparison + (qm + expr + colon + expr).setParseAction(self.push_first)[...]
        )
        assignment = Optional(assignment_op).setParseAction(self.push_last) + ternary

        self.bnf = assignment

    def eval(self, expression_string, container=None, **kwargs):

        long_kwargs = {}
        for var, value in kwargs.items():
            if isinstance(value, string_types):
                tokens = value.split(".")
                if len(tokens) == 1:
                    # Assume a single node name is the world matrix
                    value = "{}.worldMatrix[0]".format(tokens[0])
                else:
                    # Turn all attribute names into long names for consistency with
                    # results in listConnections
                    value = tokens[0]
                    for t in tokens[1:]:
                        attr = "{}.{}".format(value, t)
                        value += ".{}".format(cmds.attributeName(attr, long=True))
            long_kwargs[var] = value

        self.kwargs = long_kwargs
        # Reverse variable look up to write cleaner notes
        self._reverse_kwargs = {}
        for k, v in self.kwargs.items():
            self._reverse_kwargs[v] = k
        self.expression_string = expression_string
        self.expr_stack = []
        self.assignment_stack = []
        self.results = self.bnf.parseString(expression_string, True)
        self.container = (
            cmds.container(name=container, current=True) if container else None
        )
        self.created_nodes = {}
        stack = self.expr_stack[:] + self.assignment_stack[:]
        result = self.evaluate_stack(stack)

        if self.container:
            self.publish_container_attributes()
        return result

    def push_first(self, toks):
        self.expr_stack.append(toks[0])

    def push_last(self, toks):
        for t in toks:
            self.assignment_stack.append(t)

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
            return self.get_op_result(op, self.multiply, -1, op1)
        elif op == "?":
            # ternary
            if_false = self.evaluate_stack(s)
            if_true = self.evaluate_stack(s)
            condition = self.evaluate_stack(s)
            second_term = self.evaluate_stack(s)
            first_term = self.evaluate_stack(s)
            note = "{} {} {} ? {} : {}".format(
                first_term, self.conditionals[condition], second_term, if_true, if_false
            )

            return self.get_op_result(
                note,
                self.condition,
                first_term,
                second_term,
                condition,
                if_true,
                if_false,
                op_str=note,
            )
        elif op == ":":
            # Return the if_true statement to the ternary
            return self.evaluate_stack(s)
        elif op in "+-*/^":
            # operands are pushed onto the stack in reverse order
            op2 = self.evaluate_stack(s)
            op1 = self.evaluate_stack(s)

            return self.get_op_result(op, self.opn[op], op1, op2)
        elif op == "PI":
            return math.pi
        elif op == "E":
            return math.e
        elif op in self.fn:
            # args are pushed onto the stack in reverse order
            args = reversed([self.evaluate_stack(s) for _ in range(num_args)])
            args = list(args)
            return self.get_op_result(op, self.fn[op], *args)
        elif op[0].isalpha():
            value = self.kwargs.get(op)
            if value is None:
                raise Exception("invalid identifier '%s'" % op)
            return value
        elif op in self.conditionals:
            return self.conditionals.index(op)
        elif op == "=":
            destination = self.evaluate_stack(s)
            source = self.evaluate_stack(s)
            cmds.connectAttr(source, destination, f=True)
        else:
            # try to evaluate as int first, then as float if int fails
            try:
                return int(op)
            except ValueError:
                return float(op)

    def get_op_result(self, op, func, *args, **kwargs):
        op_str = kwargs.get("op_str", self.op_str(op, *args))
        result = self.created_nodes.get(op_str)
        if result is None:
            result = func(*args)
            self.created_nodes[op_str] = result
            self.add_notes(result, op_str)
        return result

    def add(self, v1, v2):
        return self._connect_plus_minus_average(1, v1, v2)

    def subtract(self, v1, v2):
        return self._connect_plus_minus_average(2, v1, v2)

    def _connect_plus_minus_average(self, operation, v1, v2):
        pma = cmds.createNode("plusMinusAverage")
        cmds.setAttr("{}.operation".format(pma), operation)
        in_attr = "input1D"
        out_attr = "output1D"
        # Determine whether we should use 1D or 3D attributes
        for v in [v1, v2]:
            if isinstance(v, string_types) and attribute_is_array(v):
                in_attr = "input3D"
                out_attr = "output3D"

        for i, v in enumerate([v1, v2]):
            if isinstance(v, string_types):
                if attribute_is_array(v):
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

    def sqrt(self, x):
        return self._connect_multiply_divide(3, x, 0.5)

    def _connect_multiply_divide(self, operation, v1, v2):
        mdn = cmds.createNode("multiplyDivide")
        cmds.setAttr("{}.operation".format(mdn), operation)
        value_count = 1
        # Determine whether we should use 1D or 3D attributes
        for v in [v1, v2]:
            if isinstance(v, string_types) and attribute_is_array(v):
                value_count = 3

        for i, v in enumerate([v1, v2]):
            i += 1
            if isinstance(v, string_types):
                if attribute_is_array(v):
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
        clamp = cmds.createNode("clamp")

        for v, attr in [[min_value, "min"], [max_value, "max"]]:
            if isinstance(v, string_types):
                if attribute_is_array(v):
                    cmds.connectAttr(v, "{}.{}".format(clamp, attr))
                else:
                    for x in "RGB":
                        cmds.connectAttr(v, "{}.{}{}".format(clamp, attr, x))
            else:
                for x in "RGB":
                    cmds.setAttr("{}.{}{}".format(clamp, attr, x), v)

        value_count = 1
        if isinstance(value, string_types):
            if attribute_is_array(value):
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

    def condition(self, first_term, second_term, operation, if_true, if_false):
        node = cmds.createNode("condition")
        cmds.setAttr("{}.operation".format(node), operation)

        for v, attr in [[first_term, "firstTerm"], [second_term, "secondTerm"]]:
            if isinstance(v, string_types):
                cmds.connectAttr(v, "{}.{}".format(node, attr))
            else:
                cmds.setAttr("{}.{}".format(node, attr), v)

        value_count = 1
        for v, attr in [[if_true, "colorIfTrue"], [if_false, "colorIfFalse"]]:
            if isinstance(v, string_types):
                if attribute_is_array(v):
                    value_count = 3
                    cmds.connectAttr(v, "{}.{}".format(node, attr))
                else:
                    for x in "RGB":
                        cmds.connectAttr(v, "{}.{}{}".format(node, attr, x))
            else:
                cmds.setAttr("{}.{}R".format(node, attr), v)
        return (
            "{}.outColor".format(node)
            if value_count == 3
            else "{}.outColorR".format(node)
        )

    def lerp(self, a, b, t):
        node = cmds.createNode("blendTwoAttr")

        if isinstance(t, string_types):
            cmds.connectAttr(t, "{}.attributesBlender".format(node))
        else:
            # Static value on attributesBlender doesn't make much sense
            # but we don't want to error out
            cmds.setAttr("{}.attributesBlender".format(node), t)

        for i, v in enumerate([a, b]):
            if isinstance(v, string_types):
                cmds.connectAttr(v, "{}.input[{}]".format(node, i))
            else:
                cmds.setAttr("{}.input[{}]".format(node, i), v)
        return "{}.output".format(node)

    def abs(self, x):
        return dge("x > 0 ? x : -x", x=x)

    def min(self, x, y):
        return self.condition(x, y, self.conditionals.index("<="), x, y)

    def max(self, x, y):
        return self.condition(x, y, self.conditionals.index(">="), x, y)

    def sin(self, x):
        return self._euler_to_quat(x, "X")

    def cos(self, x):
        return self._euler_to_quat(x, "W")

    def _euler_to_quat(self, x, attr):
        cmds.loadPlugin("quatNodes", qt=False)
        mdl = cmds.createNode("multDoubleLinear")
        cmds.setAttr("{}.input1".format(mdl), 2 * 57.2958)  # To degrees
        if isinstance(x, string_types):
            cmds.connectAttr(x, "{}.input2".format(mdl))
        else:
            cmds.setAttr("{}.input2".format(mdl), x)
        quat = cmds.createNode("eulerToQuat")
        cmds.connectAttr("{}.output".format(mdl), "{}.inputRotateX".format(quat))
        return "{}.outputQuat.outputQuat{}".format(quat, attr)

    def tan(self, x):
        half_pi = math.pi * 0.5
        c = dge("{} - x".format(half_pi), x=x)
        return dge("sin(x) / sin(c)", x=x, c=c)

    def acos(self, x):
        angle = cmds.createNode("angleBetween")
        for attr in ["{}{}".format(i, j) for i in [1, 2] for j in "XYZ"]:
            cmds.setAttr("{}.vector{}".format(angle, attr), 0)

        if isinstance(x, string_types):
            cmds.connectAttr(x, "{}.vector1X".format(angle))
            dge("y = x == 0.0 ? 1.0 : abs(x)", y="{}.vector2X".format(angle), x=x)
        else:
            cmds.setAttr("{}.vector1X".format(angle), x)
            cmds.setAttr("{}.vector2X".format(angle), math.fabs(x))
        dge("y = sqrt(1.0 - x*x)", y="{}.vector1Y".format(angle), x=x)
        return "{}.axisAngle.angle".format(angle)

    def asin(self, x):
        angle = cmds.createNode("angleBetween")
        for attr in ["{}{}".format(i, j) for i in [1, 2] for j in "XYZ"]:
            cmds.setAttr("{}.vector{}".format(angle, attr), 0)

        if isinstance(x, string_types):
            cmds.connectAttr(x, "{}.vector1Y".format(angle))
        else:
            cmds.setAttr("{}.vector1Y".format(angle), x)
        result = dge("sqrt(1.0 - x*x)", x=x)
        cmds.connectAttr(result, "{}.vector1X".format(angle))
        dge("y=abs(x) == 1.0 ? 1.0 : r", y="{}.vector2X".format(angle), x=x, r=result)
        return dge("x < 0 ? -y : y", x=x, y="{}.axisAngle.angle".format(angle))

    def atan(self, x):
        angle = cmds.createNode("angleBetween")
        for attr in ["{}{}".format(i, j) for i in [1, 2] for j in "XYZ"]:
            cmds.setAttr("{}.vector{}".format(angle, attr), 0)
        cmds.setAttr("{}.vector1X".format(angle), 1)
        cmds.setAttr("{}.vector2X".format(angle), 1)

        if isinstance(x, string_types):
            cmds.connectAttr(x, "{}.vector1Y".format(angle))
        else:
            cmds.setAttr("{}.vector1Y".format(angle), x)
        return dge("x < 0 ? -y : y", x=x, y="{}.axisAngle.angle".format(angle))

    def distance(self, node1, node2):
        distance_between = cmds.createNode("distanceBetween")
        cmds.connectAttr(node1, "{}.inMatrix1".format(distance_between))
        cmds.connectAttr(node2, "{}.inMatrix2".format(distance_between))
        return "{}.distance".format(distance_between)

    def add_notes(self, node, op_str):
        node = node.split(".")[0]
        attrs = cmds.listAttr(node, ud=True) or []
        if "notes" not in attrs:
            cmds.addAttr(node, ln="notes", dt="string")
        keys = self.kwargs.keys()
        keys.sort()
        notes = "Node generated by dge\n\nExpression:\n  {}\n\nOperation:\n  {}\n\nkwargs:\n  {}".format(
            self.expression_string,
            op_str,
            "\n  ".join(["{}: {}".format(x, self.kwargs[x]) for x in keys]),
        )
        cmds.setAttr("{}.notes".format(node), notes, type="string")

    def publish_container_attributes(self):
        self.add_notes(self.container, self.expression_string)
        external_connections = cmds.container(
            self.container, q=True, connectionList=True
        )
        external_connections = set(external_connections)
        container_nodes = set(cmds.container(self.container, q=True, nodeList=True))
        for var, value in self.kwargs.items():
            if not isinstance(value, string_types):
                continue
            # To connect multiple attributes to a bound container attribute, we
            # need to create an intermediary attribute that is bound and connected
            # to the internal attributes
            attr_type = attribute_type(value)
            kwargs = {"dt": attr_type} if attr_type == "matrix" else {"at": attr_type}
            cmds.addAttr(self.container, ln="_{}".format(var), **kwargs)
            published_attr = "{}._{}".format(self.container, var)
            cmds.container(self.container, e=True, publishAndBind=[published_attr, var])
            cmds.connectAttr(value, published_attr)

            # Reroute connections into the container to go through the published
            # attribute
            if value in external_connections:
                connected_nodes = set(cmds.listConnections(value, s=False, plugs=True))
                for connection in connected_nodes:
                    node_name = connection.split(".")[0]
                    if node_name in container_nodes:
                        cmds.connectAttr(published_attr, connection, force=True)

                source_plug = cmds.listConnections(value, d=False, plugs=True)
                if source_plug:
                    source_plug = source_plug[0]
                    node_name = source_plug.split(".")[0]
                    if node_name in container_nodes:
                        cmds.connectAttr(source_plug, published_attr, force=True)
                        cmds.connectAttr(published_attr, value, force=True)
        cmds.container(self.container, e=True, current=False)

    def op_str(self, op, *args):
        """Get the string form of the op and args.

        This is used for notes on the node as well as identifying which nodes can be
        reused.

        :param op: Name of the op
        :param args: Optional op arguments
        :return: The unique op string
        """
        args = [str(v) for v in args]
        if op in self.fn:
            return "{}({})".format(op, ", ".join(args))
        elif args:
            return op.join([self._reverse_kwargs.get(x, x) for x in args])
        return op


def attribute_is_array(value):
    array_types = ["double3", "float3"]
    return attribute_type(value) in array_types


def attribute_type(a):
    tokens = a.split(".")
    node = tokens[0]
    attribute = tokens[-1]
    if attribute.startswith("worldMatrix"):
        # attributeQuery doesn't seem to work with worldMatrix
        return "matrix"
    return cmds.attributeQuery(attribute, node=node, at=True)
