import io
import tokenize
from enum import Enum
from contextlib import contextmanager
from typing import Generator, Iterator, List, Set, Tuple, Optional

from .nodes import (
    STARS,
    syms,
    is_simple_decorator_expression,
    is_string_token,
    is_number_token,
)
from .lines import Line, EmptyLineTracker, LinesBlock
from .linegen import transform_line, LineGenerator, LN
from .comments import normalize_fmt_off
from .mode import (
    Mode,
    TargetVersion,
    Feature,
    supports_feature,
    VERSION_TO_FEATURES,
    FUTURE_FLAG_TO_FEATURE,
)
from .parsing import lib2to3_parse


# lib2to3 fork
from ..blib2to3.pytree import Node, Leaf
from ..blib2to3.pgen2 import token
from .trans import iter_fexpr_spans

from .._black_version import version as __version__

# types
FileContent = str
Encoding = str
NewLine = str


class WriteBack(Enum):
    NO = 0
    YES = 1
    DIFF = 2
    CHECK = 3
    COLOR_DIFF = 4

    @classmethod
    def from_configuration(
        cls, *, check: bool, diff: bool, color: bool = False
    ) -> "WriteBack":
        if check and not diff:
            return cls.CHECK

        if diff and color:
            return cls.COLOR_DIFF

        return cls.DIFF if diff else cls.YES


def format_str(src_contents: str, *, mode: Mode) -> str:
    """Reformat a string and return new contents.

    `mode` determines formatting options, such as how many characters per line are
    allowed.  Example:

    >>> import black
    >>> print(black.format_str("def f(arg:str='')->None:...", mode=black.Mode()))
    def f(arg: str = "") -> None:
        ...

    A more complex example:

    >>> print(
    ...   black.format_str(
    ...     "def f(arg:str='')->None: hey",
    ...     mode=black.Mode(
    ...       target_versions={black.TargetVersion.PY36},
    ...       line_length=10,
    ...       string_normalization=False,
    ...       is_pyi=False,
    ...     ),
    ...   ),
    ... )
    def f(
        arg: str = '',
    ) -> None:
        hey

    """
    dst_contents = _format_str_once(src_contents, mode=mode)
    # Forced second pass to work around optional trailing commas (becoming
    # forced trailing commas on pass 2) interacting differently with optional
    # parentheses.  Admittedly ugly.
    if src_contents != dst_contents:
        return _format_str_once(dst_contents, mode=mode)
    return dst_contents


def _format_str_once(src_contents: str, *, mode: Mode) -> str:
    src_node = lib2to3_parse(src_contents.lstrip(), mode.target_versions)
    dst_blocks: List[LinesBlock] = []
    if mode.target_versions:
        versions = mode.target_versions
    else:
        future_imports = get_future_imports(src_node)
        versions = detect_target_versions(src_node, future_imports=future_imports)

    context_manager_features = {
        feature
        for feature in {Feature.PARENTHESIZED_CONTEXT_MANAGERS}
        if supports_feature(versions, feature)
    }
    normalize_fmt_off(src_node)
    lines = LineGenerator(mode=mode, features=context_manager_features)
    elt = EmptyLineTracker(mode=mode)
    split_line_features = {
        feature
        for feature in {Feature.TRAILING_COMMA_IN_CALL, Feature.TRAILING_COMMA_IN_DEF}
        if supports_feature(versions, feature)
    }
    block: Optional[LinesBlock] = None
    for current_line in lines.visit(src_node):
        block = elt.maybe_empty_lines(current_line)
        dst_blocks.append(block)
        for line in transform_line(
            current_line, mode=mode, features=split_line_features
        ):
            block.content_lines.append(str(line))
    if dst_blocks:
        dst_blocks[-1].after = 0
    dst_contents = []
    for block in dst_blocks:
        dst_contents.extend(block.all_lines())
    if not dst_contents:
        # Use decode_bytes to retrieve the correct source newline (CRLF or LF),
        # and check if normalized_content has more than one line
        normalized_content, _, newline = decode_bytes(src_contents.encode("utf-8"))
        if "\n" in normalized_content:
            return newline
        return ""
    return "".join(dst_contents)


def decode_bytes(src: bytes) -> Tuple[FileContent, Encoding, NewLine]:
    """Return a tuple of (decoded_contents, encoding, newline).

    `newline` is either CRLF or LF but `decoded_contents` is decoded with
    universal newlines (i.e. only contains LF).
    """
    srcbuf = io.BytesIO(src)
    encoding, lines = tokenize.detect_encoding(srcbuf.readline)
    if not lines:
        return "", encoding, "\n"

    newline = "\r\n" if b"\r\n" == lines[0][-2:] else "\n"
    srcbuf.seek(0)
    with io.TextIOWrapper(srcbuf, encoding) as tiow:
        return tiow.read(), encoding, newline


def get_features_used(  # noqa: C901
    node: Node, *, future_imports: Optional[Set[str]] = None
) -> Set[Feature]:
    """Return a set of (relatively) new Python features used in this file.

    Currently looking for:
    - f-strings;
    - self-documenting expressions in f-strings (f"{x=}");
    - underscores in numeric literals;
    - trailing commas after * or ** in function signatures and calls;
    - positional only arguments in function signatures and lambdas;
    - assignment expression;
    - relaxed decorator syntax;
    - usage of __future__ flags (annotations);
    - print / exec statements;
    - parenthesized context managers;
    - match statements;
    - except* clause;
    - variadic generics;
    """
    features: Set[Feature] = set()
    if future_imports:
        features |= {
            FUTURE_FLAG_TO_FEATURE[future_import]
            for future_import in future_imports
            if future_import in FUTURE_FLAG_TO_FEATURE
        }

    for n in node.pre_order():
        if is_string_token(n):
            value_head = n.value[:2]
            if value_head in {'f"', 'F"', "f'", "F'", "rf", "fr", "RF", "FR"}:
                features.add(Feature.F_STRINGS)
                if Feature.DEBUG_F_STRINGS not in features:
                    for span_beg, span_end in iter_fexpr_spans(n.value):
                        if n.value[span_beg : span_end - 1].rstrip().endswith("="):
                            features.add(Feature.DEBUG_F_STRINGS)
                            break

        elif is_number_token(n):
            if "_" in n.value:
                features.add(Feature.NUMERIC_UNDERSCORES)

        elif n.type == token.SLASH:
            if n.parent and n.parent.type in {
                syms.typedargslist,
                syms.arglist,
                syms.varargslist,
            }:
                features.add(Feature.POS_ONLY_ARGUMENTS)

        elif n.type == token.COLONEQUAL:
            features.add(Feature.ASSIGNMENT_EXPRESSIONS)

        elif n.type == syms.decorator:
            if len(n.children) > 1 and not is_simple_decorator_expression(
                n.children[1]
            ):
                features.add(Feature.RELAXED_DECORATORS)

        elif (
            n.type in {syms.typedargslist, syms.arglist}
            and n.children
            and n.children[-1].type == token.COMMA
        ):
            if n.type == syms.typedargslist:
                feature = Feature.TRAILING_COMMA_IN_DEF
            else:
                feature = Feature.TRAILING_COMMA_IN_CALL

            for ch in n.children:
                if ch.type in STARS:
                    features.add(feature)

                if ch.type == syms.argument:
                    for argch in ch.children:
                        if argch.type in STARS:
                            features.add(feature)

        elif (
            n.type in {syms.return_stmt, syms.yield_expr}
            and len(n.children) >= 2
            and n.children[1].type == syms.testlist_star_expr
            and any(child.type == syms.star_expr for child in n.children[1].children)
        ):
            features.add(Feature.UNPACKING_ON_FLOW)

        elif (
            n.type == syms.annassign
            and len(n.children) >= 4
            and n.children[3].type == syms.testlist_star_expr
        ):
            features.add(Feature.ANN_ASSIGN_EXTENDED_RHS)

        elif (
            n.type == syms.with_stmt
            and len(n.children) > 2
            and n.children[1].type == syms.atom
        ):
            atom_children = n.children[1].children
            if (
                len(atom_children) == 3
                and atom_children[0].type == token.LPAR
                and atom_children[1].type == syms.testlist_gexp
                and atom_children[2].type == token.RPAR
            ):
                features.add(Feature.PARENTHESIZED_CONTEXT_MANAGERS)

        elif n.type == syms.match_stmt:
            features.add(Feature.PATTERN_MATCHING)

        elif (
            n.type == syms.except_clause
            and len(n.children) >= 2
            and n.children[1].type == token.STAR
        ):
            features.add(Feature.EXCEPT_STAR)

        elif n.type in {syms.subscriptlist, syms.trailer} and any(
            child.type == syms.star_expr for child in n.children
        ):
            features.add(Feature.VARIADIC_GENERICS)

        elif (
            n.type == syms.tname_star
            and len(n.children) == 3
            and n.children[2].type == syms.star_expr
        ):
            features.add(Feature.VARIADIC_GENERICS)

    return features


def detect_target_versions(
    node: Node, *, future_imports: Optional[Set[str]] = None
) -> Set[TargetVersion]:
    """Detect the version to target based on the nodes used."""
    features = get_features_used(node, future_imports=future_imports)
    return {
        version for version in TargetVersion if features <= VERSION_TO_FEATURES[version]
    }


def get_future_imports(node: Node) -> Set[str]:
    """Return a set of __future__ imports in the file."""
    imports: Set[str] = set()

    def get_imports_from_children(children: List[LN]) -> Generator[str, None, None]:
        for child in children:
            if isinstance(child, Leaf):
                if child.type == token.NAME:
                    yield child.value

            elif child.type == syms.import_as_name:
                orig_name = child.children[0]
                assert isinstance(orig_name, Leaf), "Invalid syntax parsing imports"
                assert orig_name.type == token.NAME, "Invalid syntax parsing imports"
                yield orig_name.value

            elif child.type == syms.import_as_names:
                yield from get_imports_from_children(child.children)

            else:
                raise AssertionError("Invalid syntax parsing imports")

    for child in node.children:
        if child.type != syms.simple_stmt:
            break

        first_child = child.children[0]
        if isinstance(first_child, Leaf):
            # Continue looking if we see a docstring; otherwise stop.
            if (
                len(child.children) == 2
                and first_child.type == token.STRING
                and child.children[1].type == token.NEWLINE
            ):
                continue

            break

        elif first_child.type == syms.import_from:
            module_name = first_child.children[1]
            if not isinstance(module_name, Leaf) or module_name.value != "__future__":
                break

            imports |= set(get_imports_from_children(first_child.children[3:]))
        else:
            break

    return imports


@contextmanager
def nullcontext() -> Iterator[None]:
    """Return an empty context manager.

    To be used like `nullcontext` in Python 3.7.
    """
    yield
