import os
from pydantic import BaseModel, validator
from rigelcore.exceptions import (
    UndeclaredEnvironmentVariableError
)
from rigel.exceptions import (
    UnsupportedCompilerError
)
from typing import Any, Dict, List


class SSHKey(BaseModel):
    """
    Information regarding a given private SSH key.

    :type hostname: string
    :cvar hostname: The URL of the host associated with the key.
    :type value: string
    :cvar value: The private SSH key.
    :type file: bool
    :cvar file: Tell if field 'value' consists of a path or a environment variable name. Default is False.
    """

    # NOTE: the validator for field 'value' assumes field 'file' to be already defined.
    # Therefore ensure that field 'file' is always declared before
    # field 'value' in the following list.

    file: bool = False
    hostname: str
    value: str

    @validator('value')
    def ensure_valid_value(cls, v: str, values: Dict[str, Any]) -> str:
        """
        Ensure that all environment variables have a value.

        :type v: string
        :param v: The value for this SSH key.
        :type values: Dict[str, Any]
        :param values: This model data.
        :rtype: string
        :return: The value for this SSH key.
        """
        if not values['file']:  # ensure value concerns an environment variable
            if not os.environ.get(v):
                raise UndeclaredEnvironmentVariableError(env=v)
        return v


class DockerSection(BaseModel):
    """
    A placeholder for information regarding how to containerize a ROS application using Docker.

    :type command: string
    :cvar command: The command to be executed once a container starts executing.
    :type distro: string
    :cvar distro: The ROS distro to be used.
    :type package: string
    :cvar package: The name of the package ROS to be containerized.
    :type image: string
    :cvar image: The name for the final Docker image.
    :type apt: List[string]
    :cvar apt: The name of dependencies to be installed using APT.
    :type compiler: string
    :cvar compiler: The tool with which to compile the containerized ROS workspace. Default value is 'catkin_make'.
    :type dir: string
    :cvar dir: The folder containing the ROS package source code, if required.
    :type entrypoint: List[string]
    :cvar entrypoint: A list of commands to be run while executing the entrypoint script.
    :type env: List[Dict[str, Any]]
    :cvar env: A list of environment variables to be set inside the Docker image.
    :type hostname: List[string]
    :type rosinstall: List[string]
    :cvar rosinstall: A list of all required .rosinstall files.
    :type ros_image: string
    :cvar ros_image: The official ROS Docker image to use as a base for the new Docker image.
    :type run: List[string]
    :cvar run: A list of commands to be executed while building the Docker image.
    :type ssh: List[rigel.files.SSHKey]
    :cvar ssh: A list of all required private SSH keys.
    :type username: string
    :cvar username: The desired username. Defaults to 'user'.
    """
    # Required fields.
    command: str
    distro: str
    image: str
    package: str

    # Optional fields.
    ros_image: str
    apt: List[str] = []
    compiler: str = 'catkin_make'
    dir: str = ''
    entrypoint: List[str] = []
    env: List[Dict[str, Any]] = []
    hostname: List[str] = []
    rosinstall: List[str] = []
    run: List[str] = []
    ssh: List[SSHKey] = []
    username: str = 'rigeluser'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if not kwargs.get('ros_image') and kwargs.get('distro'):
            kwargs['ros_image'] = kwargs['distro']
        super().__init__(*args, **kwargs)

    @validator('compiler')
    def validate_compiler(cls, compiler: str) -> str:
        """
        Ensure that the specified ROS package compiler used is supported by Rigel.

        :type compiler: string
        :param compiler: ROS package compiler.
        """
        # NOTE: At the moment only "catkin" and "colcon" are supported.
        if compiler not in ['catkin_make', 'colcon']:
            raise UnsupportedCompilerError(compiler=compiler)
        return compiler


class DockerfileSection(BaseModel):
    """
    A placeholder for information regarding building Docker images using an existing Dockerfile.

    :type dockerfile: str
    :cvar dockerfile: The path to a Dockerfile.
    :type image: str
    :cvar image: The name for the final Docker image.
    :type package: str
    :cvar package: The name of the package ROS to be containerized.
    """
    # Required fields.
    dockerfile: str
    image: str
    package: str
