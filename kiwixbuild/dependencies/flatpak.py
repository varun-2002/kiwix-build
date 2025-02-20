import os

from .base import Dependency, NoopSource, Builder
from kiwixbuild.utils import Remotefile, add_execution_right, run_command

pj = os.path.join

class org_kde(Dependency):
    neutral = False
    name = 'org.kde'

    Source = NoopSource

    class Builder(Builder):
        def _setup_remote(self, context):
            command = "flatpak --user remote-add --if-not-exists {remote_name} {remote_url}"
            command = command.format(
                remote_name = 'flathub',
                remote_url = 'https://flathub.org/repo/flathub.flatpakrepo'
            )
            env = self.buildEnv.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=False)
            run_command(command, self.buildEnv.build_dir, context, env=env)

        def _install_sdk(self, context):
            command = "flatpak --user install -y {remote_name} {name}.Sdk//{version} {name}.Platform//{version}"
            command = command.format(
                remote_name = 'flathub',
                name = self.target.name,
                version = self.target.version()
            )
            env = self.buildEnv.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=False)
            run_command(command, self.buildEnv.build_dir, context, env=env)

        def build(self):
            self.command('setup_remote', self._setup_remote)
            self.command('install_sdk', self._install_sdk)


class io_qt_qtwebengine(Dependency):
    neutral = False
    name = 'io.qt.qtwebengine'

    Source = NoopSource

    class Builder(Builder):
        def _setup_remote(self, context):
            command = "flatpak --user remote-add --if-not-exists {remote_name} {remote_url}"
            command = command.format(
                remote_name = 'flathub',
                remote_url = 'https://flathub.org/repo/flathub.flatpakrepo'
            )
            env = self.buildEnv.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=False)
            run_command(command, self.buildEnv.build_dir, context, env=env)

        def _install_sdk(self, context):
            command = "flatpak --user install -y {remote_name} {name}.BaseApp//{version}"
            command = command.format(
                remote_name = 'flathub',
                name = self.target.name,
                version = self.target.version()
            )
            env = self.buildEnv.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=False)
            run_command(command, self.buildEnv.build_dir, context, env=env)

        def build(self):
            self.command('setup_remote', self._setup_remote)
            self.command('install_sdk', self._install_sdk)

