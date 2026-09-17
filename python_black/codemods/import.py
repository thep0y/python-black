import argparse

import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand


class RewriteImportsCommand(VisitorBasedCodemodCommand):
    DESCRIPTION: str = "rewrite imports."

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        # Add command-line args that a user can specify for running this
        # codemod.
        arg_parser.add_argument(
            "--replace",
            dest="replacements",
            metavar="STRING",
            help="modules to replacement",
            action="append",
            required=True,
        )
        arg_parser.add_argument(
            "--relative-to",
            dest="relative_to",
            metavar="STRING",
            help="make the imports point to this path",
            required=True,
        )

    def __init__(
        self, context: CodemodContext, replacements: list[str], relative_to: str
    ) -> None:
        super().__init__(context)
        self.replacements = replacements
        self.relative_to = relative_to

    def _get_module_name(self, module: cst.Attribute | cst.Name) -> str | None:
        if module is not None:
            while isinstance(module, cst.Attribute):
                module = module.value
            return module.value
        return None

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        if self._get_module_name(updated_node.module) in self.replacements:
            extra_dots = self.context.full_package_name.removeprefix(self.relative_to).lstrip(".").count(".")
            relative = [cst.Dot(), cst.Dot()] + [cst.Dot() for _ in range(extra_dots)]
            return updated_node.with_changes(relative=relative)

        return updated_node

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> cst.Import:
        for each in updated_node.names:
            if self._get_module_name(each.name) in self.replacements:
                if not isinstance(each.name, cst.Name):
                    raise ValueError("Rewriting submodule imports not supported")
                if len(updated_node.names) > 1:
                    raise ValueError("Rewriting multiple imports on the same line is not supported")

                relative_to, last = self.relative_to.rsplit(".", 1)
                extra_dots = self.context.full_package_name.removeprefix(relative_to).lstrip(".").count(".")
                return cst.ImportFrom(
                    module=cst.Name(value=last),
                    relative=[cst.Dot(), cst.Dot()] + [cst.Dot() for _ in range(extra_dots)],
                    names=[each]
                )
        return updated_node
