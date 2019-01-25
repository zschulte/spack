# Copyright 2013-2018 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *
import os


class Openjdk(Package):
    """The free and opensource java implementation"""

    homepage = "https://jdk.java.net"

    version(
        "11.0.2",
        sha256="99be79935354f5c0df1ad293620ea36d13f48ec3ea870c838f20c504c9668b57",
        url="https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_linux-x64_bin.tar.gz",
        preferred=True,
    )

    version(
        "11.0.1",
        sha256="7a6bb980b9c91c478421f865087ad2d69086a0583aeeb9e69204785e8e97dcfd",
        url="https://download.java.net/java/GA/jdk11/13/GPL/openjdk-11.0.1_linux-x64_bin.tar.gz",
    )

    version(
        "1.8.0_202-b03",
        sha256="e535ff66bca1623937e833ed3651d03acb09da9faf5ecc514e66ec8344030494",
        url="https://download.java.net/java/early_access/jdk8/b03/BCL/jdk-8u202-ea-bin-b03-linux-x64-07_nov_2018.tar.gz",
    )

    provides("java")
    provides("java@11", when="@11.0:11.99")
    provides("java@8", when="@1.8.0:1.8.999")

    # FIXME:
    # 1. `extends('java')` doesn't work, you need to use `extends('openjdk')`
    # 2. Packages cannot extend multiple packages, see #987
    # 3. Update `YamlFilesystemView.merge` to allow a Package to completely
    #    override how it is symlinked into a view prefix. Then, spack activate
    #    can symlink all *.jar files to `prefix.lib.ext`
    extendable = True

    @property
    def home(self):
        """Most of the time, ``JAVA_HOME`` is simply ``spec['java'].prefix``.
        However, if the user is using an externally installed JDK, it may be
        symlinked. For example, on macOS, the ``java`` executable can be found
        in ``/usr/bin``, but ``JAVA_HOME`` is actually
        ``/Library/Java/JavaVirtualMachines/jdk-10.0.1.jdk/Contents/Home``.
        Users may not know the actual installation directory and add ``/usr``
        to their ``packages.yaml`` unknowingly. Run ``java_home`` if it exists
        to determine exactly where it is installed. Specify which version we
        are expecting in case multiple Java versions are installed.
        See ``man java_home`` for more details."""

        prefix = self.prefix
        java_home = prefix.libexec.java_home
        if os.path.exists(java_home):
            java_home = Executable(java_home)
            version = str(self.version.up_to(2))
            prefix = java_home("--version", version, output=str).strip()
            prefix = Prefix(prefix)

        return prefix

    @property
    def libs(self):
        """Depending on the version number and whether the full JDK or just
        the JRE was installed, Java libraries can be in several locations:
        * ``lib/libjvm.so``
        * ``jre/lib/libjvm.dylib``
        Search recursively to find the correct library location."""

        return find_libraries(["libjvm"], root=self.home, recursive=True)

    def install(self, spec, prefix):
        install_tree(".", prefix)

    def setup_environment(self, spack_env, run_env):
        """Set JAVA_HOME."""

        run_env.set("JAVA_HOME", self.home)

    def setup_dependent_environment(self, spack_env, run_env, dependent_spec):
        """Set JAVA_HOME and CLASSPATH.
        CLASSPATH contains the installation prefix for the extension and any
        other Java extensions it depends on."""

        spack_env.set("JAVA_HOME", self.home)

        class_paths = []
        for d in dependent_spec.traverse(deptype=("build", "run", "test")):
            if d.package.extends(self.spec):
                class_paths.extend(find(d.prefix, "*.jar"))

        classpath = os.pathsep.join(class_paths)
        spack_env.set("CLASSPATH", classpath)

        # For runtime environment set only the path for
        # dependent_spec and prepend it to CLASSPATH
        if dependent_spec.package.extends(self.spec):
            class_paths = find(dependent_spec.prefix, "*.jar")
            classpath = os.pathsep.join(class_paths)
            run_env.prepend_path("CLASSPATH", classpath)

    def setup_dependent_package(self, module, dependent_spec):
        """Allows spec['java'].home to work."""

        self.spec.home = self.home
