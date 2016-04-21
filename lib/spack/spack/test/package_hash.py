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
import unittest
import re

from spack.test.mock_packages_test import *
from spack.util.package_hash import package_hash, package_content

class PackageHashTest(MockPackagesTest):
    def test_hash(self):
        package_hash("hash-test1@1.2")
    
    def test_different_variants(self):
        spec1 = Spec("hash-test1@1.2 +variantx")
        spec2 = Spec("hash-test1@1.2 +varianty")
        self.assertEqual(package_hash(spec1), 
            package_hash(spec2))

    def test_all_same_but_name(self):
        spec1 = Spec("hash-test1@1.2")
        spec2 = Spec("hash-test2@1.2")
        self.compare_sans_name(self.assertEqual, spec1, spec2)
        
        spec1 = Spec("hash-test1@1.2 +varianty")
        spec2 = Spec("hash-test2@1.2 +varianty")
        self.compare_sans_name(self.assertEqual, spec1, spec2)

    def test_all_same_but_archive_hash(self):
        """
        Archive hash is not intended to be reflected in Package hash.
        """
        spec1 = Spec("hash-test1@1.3")
        spec2 = Spec("hash-test2@1.3")
        self.compare_sans_name(self.assertEqual, spec1, spec2)

    def test_all_same_but_patch_contents(self):
        spec1 = Spec("hash-test1@1.1")
        spec2 = Spec("hash-test2@1.1")
        self.compare_sans_name(self.assertEqual, spec1, spec2)

    def test_all_same_but_patches_to_apply(self):
        spec1 = Spec("hash-test1@1.4")
        spec2 = Spec("hash-test2@1.4")
        self.compare_sans_name(self.assertEqual, spec1, spec2)

    def test_all_same_but_install(self):
        spec1 = Spec("hash-test1@1.5")
        spec2 = Spec("hash-test2@1.5")
        self.compare_sans_name(self.assertNotEqual, spec1, spec2)

    def compare_sans_name(self, assertFunc, spec1, spec2):
        content1 = package_content(spec1, remove_pkg_name=True)
        content2 = package_content(spec2, remove_pkg_name=True)
        assertFunc(content1, content2)
    
