# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Subversion(Package):
    """Apache Subversion - an open source version control system."""
    homepage = 'https://subversion.apache.org/'
    url = 'http://archive.apache.org/dist/subversion/subversion-1.8.13.tar.gz'

    version('1.9.7',     '1a5f48acf9d0faa60e8c7aea96a9b29ab1d4dcac')
    version('1.9.6',     '89e1b3f9d79422c094ccb95769360d5fe7df2bb1')
    version('1.9.5',     'ac9f8ee235f1b667dd6506864af8035aaedfc2d9')
    version('1.9.3',     'a92bcfaec4e5038f82c74a7b5bbd2f46')
    version('1.8.17',    'd1f8d45f97168d6271c58c5b25421cc32954c81b')
    version('1.8.13',    '8065b3698d799507fb72dd7926ed32b6')

    variant('perl', default=False, description='Build with Perl bindings')

    depends_on('apr')
    depends_on('apr-util')
    depends_on('zlib')
    depends_on('sqlite')
    depends_on('serf')

    extends('perl', when='+perl')
    depends_on('swig@1.3.24:3.0.0', when='+perl')
    depends_on('perl-term-readkey', when='+perl')

    # Optional: We need swig if we want the Perl, Python or Ruby
    # bindings.
    # depends_on('swig')
    # depends_on('python')
    # depends_on('perl')
    # depends_on('ruby')

    # Installation has race cases.
    parallel = False

    def install(self, spec, prefix):

        # configure, build, install:
        # Ref:
        # http://www.linuxfromscratch.org/blfs/view/svn/general/subversion.html
        options = ['--prefix=%s' % prefix]
        options.append('--with-apr=%s' % spec['apr'].prefix)
        options.append('--with-apr-util=%s' % spec['apr-util'].prefix)
        options.append('--with-zlib=%s' % spec['zlib'].prefix)
        options.append('--with-sqlite=%s' % spec['sqlite'].prefix)
        options.append('--with-serf=%s' % spec['serf'].prefix)

        if 'swig' in spec:
            options.append('--with-swig=%s' % spec['swig'].prefix)
        if 'perl' in spec:
            options.append('PERL=%s' % spec['perl'].command.path)

        configure(*options)
        make()
        if self.run_tests:
            make('check')
        make('install')

        if spec.satisfies('+perl'):
            make('swig-pl')
            if self.run_tests:
                make('check-swig-pl')
            make('install-swig-pl-lib')
            with working_dir(join_path(
                    'subversion', 'bindings', 'swig', 'perl', 'native')):
                perl = which('perl')
                perl('Makefile.PL', 'INSTALL_BASE=%s' % prefix)
                make('install')

        # python bindings
        # make('swig-py',
        #     'swig-pydir=/usr/lib/python2.7/site-packages/libsvn',
        #     'swig_pydir_extra=/usr/lib/python2.7/site-packages/svn')
        # make('install-swig-py',
        #     'swig-pydir=/usr/lib/python2.7/site-packages/libsvn',
        #     'swig_pydir_extra=/usr/lib/python2.7/site-packages/svn')

        # ruby bindings
        # make('swig-rb')
        # make('isntall-swig-rb')
