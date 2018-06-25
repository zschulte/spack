##############################################################################
# Copyright (c) 2013-2018, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Spack.
# Created by Todd Gamblin, tgamblin@llnl.gov, All rights reserved.
# LLNL-CODE-647188
#
# For details, see https://github.com/spack/spack
# Please also see the NOTICE and LICENSE files for our notice and the LGPL.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License (as
# published by the Free Software Foundation) version 2.1, February 1999.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the terms and
# conditions of the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##############################################################################
import pytest
import subprocess
import os
import tempfile

from spack.util.module_cmd import (
    module
    get_path_from_module,
    get_argument_from_module_line
)

typeset_func = subprocess.Popen('module avail',
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
typeset_func.wait()
typeset = typeset_func.stderr.read()
MODULE_DEFINED = b'not found' not in typeset

test_module_lines = ['prepend-path LD_LIBRARY_PATH /path/to/lib',
                     'setenv MOD_DIR /path/to',
                     'setenv LDFLAGS -Wl,-rpath/path/to/lib',
                     'setenv LDFLAGS -L/path/to/lib',
                     'prepend-path PATH /path/to/bin']


@pytest.fixture
def save_env():
    old_path = os.environ.get('PATH', None)
    old_bash_func = os.environ.get('BASH_FUNC_module()', None)

    yield

    if old_path:
        os.environ['PATH'] = old_path
    if old_bash_func:
        os.environ['BASH_FUNC_module()'] = old_bash_func


@pytest.fixture
def tmp_module():
    module_dir = tempfile.mkdtemp()
    module_file = os.path.join(module_dir, 'mod')

    module('use', module_dir)

    yield module_file

    module('unuse', module_dir)
    os.remove(module_file)
    os.rmdir(module_dir)


@pytest.mark.skipif(not MODULE_DEFINED, reason='Requires module() function')
def test_get_path_from_module(tmp_module):
    for line in test_module_lines:
        with open(tmp_module, 'w') as f:
            f.truncate()
            f.write('#%Module1.0\n')
            f.write(line)

        path = get_path_from_module(os.path.basename(tmp_module))
        assert path == '/path/to'


@pytest.mark.skipif(MODULE_DEFINED, reason='Only works if module() undefined')
def test_get_path_from_module_faked(save_env):
    for line in test_module_lines:
        module_func = '() { eval `echo ' + line + ' bash filler`\n}'
        os.environ['BASH_FUNC_module()'] = module_func
        path = get_path_from_module('mod')
        assert path == '/path/to'

    os.environ['BASH_FUNC_module()'] = '() { eval $(echo fill bash $*)\n}'
    path = get_path_from_module('mod')

    assert path is None


def test_get_path_from_module_contents():
    # A line with "MODULEPATH" appears early on, and the test confirms that it
    # is not extracted as the package's path
    module_show_output = """
os.environ["MODULEPATH"] = "/path/to/modules1:/path/to/modules2";
----------------------------------------------------------------------------
   /root/cmake/3.9.2.lua:
----------------------------------------------------------------------------
help([[CMake Version 3.9.2
]])
whatis("Name: CMake")
whatis("Version: 3.9.2")
whatis("Category: Tools")
whatis("URL: https://cmake.org/")
prepend_path("PATH","/path/to/cmake-3.9.2/bin")
prepend_path("MANPATH","/path/to/cmake/cmake-3.9.2/share/man")
"""
    module_show_lines = module_show_output.split('\n')
    assert (get_path_from_module_contents(module_show_lines, 'cmake-3.9.2') ==
            '/path/to/cmake-3.9.2')


def test_pkg_dir_from_module_name():
    module_show_lines = ['setenv FOO_BAR_DIR /path/to/foo-bar']

    assert (get_path_from_module_contents(module_show_lines, 'foo-bar') ==
            '/path/to/foo-bar')

    assert (get_path_from_module_contents(module_show_lines, 'foo-bar/1.0') ==
            '/path/to/foo-bar')


def test_get_argument_from_module_line():
    lines = ['prepend-path LD_LIBRARY_PATH /lib/path',
             'prepend-path  LD_LIBRARY_PATH  /lib/path',
             "prepend_path('PATH' , '/lib/path')",
             'prepend_path( "PATH" , "/lib/path" )',
             'prepend_path("PATH",' + "'/lib/path')"]

    bad_lines = ['prepend_path(PATH,/lib/path)',
                 'prepend-path (LD_LIBRARY_PATH) /lib/path']

    assert all(get_path_arg_from_module_line(l) == '/lib/path' for l in lines)
    for bl in bad_lines:
        with pytest.raises(ValueError):
            get_argument_from_module_line(bl)
