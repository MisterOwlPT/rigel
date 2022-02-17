import click
import docker
import os
import sys
from pathlib import Path
from rigel.docker import ImageBuilder
from rigel.exceptions import (
    RigelfileAlreadyExistsError,
    RigelError
)
from rigel.files import (
    Renderer,
    RigelfileCreator,
    YAMLDataDecoder,
    YAMLDataLoader
)
from rigel.loggers import ErrorLogger, MessageLogger
from rigel.models import ModelBuilder, Rigelfile, PluginSection
from rigel.plugins import PluginInstaller
from typing import Any, List

from rigel.plugins.loader import PluginLoader


def create_folder(path: str) -> None:
    """
    Create a folder in case it does not exist yet.

    :type path: string
    :param path: Path of the folder to be created.
    """
    Path(path).mkdir(parents=True, exist_ok=True)


# TODO: change return type to Rigelfile
def parse_rigelfile() -> Any:
    """
    Parse information inside local Rigelfile.

    :rtype: rigle.models.Rigelfile
    :return: The parsed information.
    """
    loader = YAMLDataLoader('./Rigelfile')
    decoder = YAMLDataDecoder()

    yaml_data = decoder.decode(loader.load())

    builder = ModelBuilder(Rigelfile)
    return builder.build([], yaml_data)


def create_docker_client() -> docker.api.client.APIClient:
    """
    Create a Docker client intance.

    :rtype docker.api.client.APIClient
    ::return: A docker client instance.
    """
    return docker.from_env().api


def rigelfile_exists() -> bool:
    """
    Verify if a Rigelfile is present.

    :rtype: bool
    :return: True if a Rigelfile is found at the current directory. False otherwise.
    """
    return os.path.isfile('./Rigelfile')


def run_plugins(plugins: List[PluginSection]) -> None:
    """
    Run a set of external plugins.

    :rtype plugins: List[rigel.plugin.Plugin]
    :return plugins: List of external plugins to be run.
    """
    try:

        if plugins:
            for plugin in plugins:
                MessageLogger().info(f'Using external plugin {plugin.__class__.__module__}.{plugin.__class__.__name__}')
                loader = PluginLoader()
                plugin_instance = loader.load(plugin)
                plugin_instance.run()
        else:
            MessageLogger().warning('No plugin was declared.')

    except RigelError as err:
        ErrorLogger().log(err)
        sys.exit(err.code)


@click.group()
def cli() -> None:
    """
    Rigel - containerize and deploy your ROS application using Docker
    """
    pass


@click.command()
@click.option('--force', is_flag=True, default=False, help='Write over an existing Rigelfile.',)
def init(force: bool) -> None:
    """
    Create an empty Rigelfile.
    """
    try:

        if rigelfile_exists() and not force:
            raise RigelfileAlreadyExistsError()

        rigelfile_creator = RigelfileCreator()
        rigelfile_creator.create()
        print('Rigelfile created with success.')

    except RigelfileAlreadyExistsError as err:
        ErrorLogger().log(err)
        sys.exit(err.code)


@click.command()
def create() -> None:
    """
    Create all files required to containerize your ROS application.
    """

    create_folder('.rigel_config')

    try:

        rigelfile = parse_rigelfile()

        renderer = Renderer(rigelfile.build)
        renderer.render('Dockerfile.j2', 'Dockerfile')
        renderer.render('entrypoint.j2', 'entrypoint.sh')
        if rigelfile.build.ssh:
            renderer.render('config.j2', 'config')

    except RigelError as err:
        ErrorLogger().log(err)
        sys.exit(err.code)


@click.command()
def build() -> None:
    """
    Build a Docker image with your ROS application.
    """

    rigelfile = parse_rigelfile()
    docker_client = create_docker_client()

    try:
        builder = ImageBuilder(docker_client)
        builder.build(rigelfile.build)

    except RigelError as err:
        ErrorLogger().log(err)
        sys.exit(err.code)


@click.command()
def deploy() -> None:
    """
    Push a Docker image to a remote image registry.
    """
    rigelfile = parse_rigelfile()
    run_plugins(rigelfile.deploy)


@click.command()
def run() -> None:
    """
    Start your containerized ROS application.
    """
    rigelfile = parse_rigelfile()
    run_plugins(rigelfile.simulation_plugins)


# rigel install MisterOwlPT.ecr_rigel_plugin
# rigel install --host gitlab.inesctec.pt --ssh pedro.m.melo.ecr_rigel_plugin
@click.command()
@click.argument('plugin', type=str)
@click.option('--host', type=str, default='github.com', help='The repository where the plugin is hosted.')
@click.option('--ssh', is_flag=True, default=False, help='Download plugin using SSH instead of HTTPS.')
def install(plugin: str, host: str, ssh: bool) -> None:
    """
    Install external plugins.
    """

    try:
        installer = PluginInstaller(plugin, host, ssh)
        installer.install()
    except RigelError as err:
        ErrorLogger().log(err)
        sys.exit(err.code)


# Add commands to CLI
cli.add_command(init)
cli.add_command(build)
cli.add_command(create)
cli.add_command(deploy)
cli.add_command(install)
cli.add_command(run)


def main() -> None:
    """
    Rigel application entry point.
    """
    cli()


if __name__ == '__main__':
    main()
