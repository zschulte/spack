##############################################################################
# Copyright (c) 2016, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Spack.
# Written by Todd Gamblin, tgamblin@llnl.gov, All rights reserved.
# LLNL-CODE-647188
#
# For details, see https://software.llnl.gov/spack
# Please also see the LICENSE file for our notice and the LGPL.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License (as published by
# the Free Software Foundation) version 2.1 dated February 1999.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the terms and
# conditions of the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##############################################################################
import spack
from spack import Package
from spack.directives import directives
from spack.error import SpackError
from spack.spec import Spec
from spack.util.naming import mod_to_class


import ast
import hashlib
import sys
import unparse

attributes = ['homepage', 'url', 'list_url', 'extendable', 'parallel', 'make_jobs']

class RemoveDocstrings(ast.NodeTransformer):
    """Transformer that removes docstrings from a Python AST."""
    def remove_docstring(self, node):
        if node.body:
            if isinstance(node.body[0], ast.Expr) and \
               isinstance(node.body[0].value, ast.Str):
                node.body.pop(0)

        self.generic_visit(node)
        return node
    def visit_FunctionDef(self, node): return self.remove_docstring(node)
    def visit_ClassDef(self, node):    return self.remove_docstring(node)
    def visit_Module(self, node):      return self.remove_docstring(node)


class RemoveDirectives(ast.NodeTransformer):
    """Remove Spack directives from a package AST."""
    def __init__(self, pkg_name):
        self.pkg_name = pkg_name

    def is_directive(self, node):
        return (isinstance(node, ast.Expr) and
                node.value and isinstance(node.value, ast.Call) and
                node.value.func.id in directives)

    def is_spack_attribute(self, node):
        return (isinstance(node, ast.Assign) and
                node.targets and isinstance(node.targets[0], ast.Name) and
                node.targets[0].id in attributes)

    def visit_ClassDef(self, node):
        if node.name == mod_to_class(self.pkg_name):
            node.body = [
                c for c in node.body
                if (not self.is_directive(c) and not self.is_spack_attribute(c))]
        return node


class TagMultiMethods(ast.NodeVisitor):
    def __init__(self, spec):
        self.spec = spec
        self.methods = {}

    def visit_FunctionDef(self, node):
        nodes = self.methods.setdefault(node.name, [])
        if node.decorator_list:
            dec = node.decorator_list[0]
            if isinstance(dec, ast.Call) and dec.func.id == 'when':
                cond = dec.args[0].s
                nodes.append((node, self.spec.satisfies(cond, strict=True)))
        else:
            nodes.append((node, None))


class ResolveMultiMethods(ast.NodeTransformer):
    def __init__(self, methods):
        self.methods = methods

    def resolve(self, node):
        if node.name not in self.methods:
            print "WAT", node.name, node
            return node

        result = None
        for n, cond in self.methods[node.name]:
            if cond: return n
            if cond is None: result = n
        return result

    def visit_FunctionDef(self, node):
        if self.resolve(node) is node:
            node.decorator_list = []
            return node
        return None

import StringIO
def to_source(spec):
    output = StringIO.StringIO()
    unparse.Unparser(package_ast(spec), file=output)
    return output.getvalue()

def package_content(spec):
    return ast.dump(package_ast(spec))
    
def package_hash(spec):
    return hashlib.md5(package_content(spec))

def package_ast(spec):
    spec = Spec(spec)
    p = spec.package

    filename = spack.repo.filename_for_package_name(spec.name)
    with open(filename) as f:
        text = f.read()
        root = ast.parse(text)

    root = RemoveDocstrings().visit(root)

    RemoveDirectives(spec.name).visit(root)

    fmm = TagMultiMethods(spec)
    fmm.visit(root)

    root = ResolveMultiMethods(fmm.methods).visit(root)
    return root

class PackageHashError(SpackError):
    def __init__(self, msg):
        super(PackageHashError, self).__init__(
            "Package hashing error: %s" % msg)

