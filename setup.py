from setuptools import setup, find_packages


def get_version():
    with open('version', 'r') as fp:
        return fp.read()


def get_requirements():
    """
    Loads requirements from file.

    Kept separately to allow for Dockerfile caching.

    :return: Contents of requirements file as string.
    """
    with open('requirements.txt', 'r') as fp:
        return fp.read()


setup(
    name="dht-python",
    version=get_version(),
    packages=find_packages(),
    install_requirements=get_requirements(),
    extras_require={
        'test': ['pytest', 'pytest-cov']
    }
)
