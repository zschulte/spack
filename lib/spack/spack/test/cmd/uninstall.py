# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import pytest
import spack.store
from spack.main import SpackCommand, SpackCommandError

uninstall = SpackCommand('uninstall')
install = SpackCommand('install')


class MockArgs(object):

    def __init__(self, packages, all=False, force=False, dependents=False):
        self.packages = packages
        self.all = all
        self.force = force
        self.dependents = dependents
        self.yes_to_all = True


@pytest.mark.db
def test_multiple_matches(database):
    """Test unable to uninstall when multiple matches."""
    with pytest.raises(SpackCommandError):
        uninstall('-y', 'mpileaks')


@pytest.mark.db
def test_installed_dependents(database):
    """Test can't uninstall when ther are installed dependents."""
    with pytest.raises(SpackCommandError):
        uninstall('-y', 'libelf')


@pytest.mark.db
def test_recursive_uninstall(database):
    """Test recursive uninstall."""
    uninstall('-y', '-a', '--dependents', 'callpath')

    all_specs = spack.store.layout.all_specs()
    assert len(all_specs) == 8
    # query specs with multiple configurations
    mpileaks_specs = [s for s in all_specs if s.satisfies('mpileaks')]
    callpath_specs = [s for s in all_specs if s.satisfies('callpath')]
    mpi_specs = [s for s in all_specs if s.satisfies('mpi')]

    assert len(mpileaks_specs) == 0
    assert len(callpath_specs) == 0
    assert len(mpi_specs) == 3


@pytest.mark.db
def test_force_uninstall(database):
    """Test forced uninstall and reinstall of old specs."""
    # this is the spec to be removed
    callpath_spec = spack.store.db.query_one('callpath ^mpich')
    dag_hash = callpath_spec.dag_hash()

    # ensure can look up by hash and that it's a dependent of mpileaks
    def validate_callpath_spec():
        specs = spack.store.db.get_by_hash(dag_hash)
        assert len(specs) == 1 and specs[0] == callpath_spec

        specs = spack.store.db.get_by_hash(dag_hash[:7])
        assert len(specs) == 1 and specs[0] == callpath_spec

        mpileaks_spec = spack.store.db.query_one('mpileaks ^mpich')
        assert callpath_spec in mpileaks_spec

    validate_callpath_spec()

    uninstall('-y', '-f', 'callpath ^mpich')

    # ensure that you can still look up by hash and see deps, EVEN though
    # the callpath spec is missing.
    validate_callpath_spec()

    # BUT, make sure that the removed callpath spec is not in queries
    def db_specs():
        all_specs = spack.store.layout.all_specs()
        return (
            all_specs,
            [s for s in all_specs if s.satisfies('mpileaks')],
            [s for s in all_specs if s.satisfies('callpath')],
            [s for s in all_specs if s.satisfies('mpi')]
        )
    all_specs, mpileaks_specs, callpath_specs, mpi_specs = db_specs()
    assert len(all_specs) == 13
    assert len(mpileaks_specs) == 3
    assert len(callpath_specs) == 2
    assert len(mpi_specs) == 3

    # Now, REINSTALL the spec and make sure everything still holds
    install('--fake', '/%s' % dag_hash[:7])

    validate_callpath_spec()

    all_specs, mpileaks_specs, callpath_specs, mpi_specs = db_specs()
    assert len(all_specs) == 14      # back to 14
    assert len(mpileaks_specs) == 3
    assert len(callpath_specs) == 3  # back to 3
    assert len(mpi_specs) == 3
