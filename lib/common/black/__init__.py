from contextlib import contextmanager
import io
import tokenize
from typing import Generator, Iterator, List, Set, Tuple


from black.nodes import STARS, syms, is_simple_decorator_expression
from black.lines import Line, EmptyLineTracker
from black.linegen import transform_line, LineGenerator, LN
from black.comments import normalize_fmt_off
from black.mode import Mode, TargetVersion
from black.mode import Feature, supports_feature, VERSION_TO_FEATURES
from black.parsing import lib2to3_parse


# lib2to3 fork
from blib2to3.pytree import Node, Leaf
from blib2to3.pgen2 import token

from _black_version import version as __version__

# types
FileContent = str
Encoding = str
NewLine = str


def format_str(src_contents: str, *, mode: Mode) -> FileContent:
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
    src_node = lib2to3_parse(src_contents.lstrip(), mode.target_versions)
    dst_contents = []
    future_imports = get_future_imports(src_node)
    if mode.target_versions:
        versions = mode.target_versions
    else:
        versions = detect_target_versions(src_node)
    normalize_fmt_off(src_node)
    lines = LineGenerator(
        mode=mode,
        remove_u_prefix="unicode_literals" in future_imports or supports_feature(versions, Feature.UNICODE_LITERALS),
    )
    elt = EmptyLineTracker(is_pyi=mode.is_pyi)
    empty_line = Line(mode=mode)
    after = 0
    split_line_features = {
        feature
        for feature in {Feature.TRAILING_COMMA_IN_CALL, Feature.TRAILING_COMMA_IN_DEF}
        if supports_feature(versions, feature)
    }
    for current_line in lines.visit(src_node):
        dst_contents.append(str(empty_line) * after)
        before, after = elt.maybe_empty_lines(current_line)
        dst_contents.append(str(empty_line) * before)
        for line in transform_line(current_line, mode=mode, features=split_line_features):
            dst_contents.append(str(line))
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


def get_features_used(node: Node) -> Set[Feature]:
    """Return a set of (relatively) new Python features used in this file.

    Currently looking for:
    - f-strings;
    - underscores in numeric literals;
    - trailing commas after * or ** in function signatures and calls;
    - positional only arguments in function signatures and lambdas;
    - assignment expression;
    - relaxed decorator syntax;
    """
    features: Set[Feature] = set()
    for n in node.pre_order():
        if n.type == token.STRING:
            value_head = n.value[:2]  # type: ignore
            if value_head in {'f"', 'F"', "f'", "F'", "rf", "fr", "RF", "FR"}:
                features.add(Feature.F_STRINGS)

        elif n.type == token.NUMBER:
            if "_" in n.value:  # type: ignore
                features.add(Feature.NUMERIC_UNDERSCORES)

        elif n.type == token.SLASH:
            if n.parent and n.parent.type in {syms.typedargslist, syms.arglist}:
                features.add(Feature.POS_ONLY_ARGUMENTS)

        elif n.type == token.COLONEQUAL:
            features.add(Feature.ASSIGNMENT_EXPRESSIONS)

        elif n.type == syms.decorator:
            if len(n.children) > 1 and not is_simple_decorator_expression(n.children[1]):
                features.add(Feature.RELAXED_DECORATORS)

        elif n.type in {syms.typedargslist, syms.arglist} and n.children and n.children[-1].type == token.COMMA:
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

    return features


def detect_target_versions(node: Node) -> Set[TargetVersion]:
    """Detect the version to target based on the nodes used."""
    features = get_features_used(node)
    return {version for version in TargetVersion if features <= VERSION_TO_FEATURES[version]}


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


def patch_click() -> None:
    """Make Click not crash on Python 3.6 with LANG=C.

    On certain misconfigured environments, Python 3 selects the ASCII encoding as the
    default which restricts paths that it can access during the lifetime of the
    application.  Click refuses to work in this scenario by raising a RuntimeError.

    In case of Black the likelihood that non-ASCII characters are going to be used in
    file paths is minimal since it's Python source code.  Moreover, this crash was
    spurious on Python 3.7 thanks to PEP 538 and PEP 540.
    """
    try:
        from click import core
        from click import _unicodefun  # type: ignore
    except ModuleNotFoundError:
        return

    for module in (core, _unicodefun):
        if hasattr(module, "_verify_python3_env"):
            module._verify_python3_env = lambda: None  # type: ignore
        if hasattr(module, "_verify_python_env"):
            module._verify_python_env = lambda: None  # type: ignore
