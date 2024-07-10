"""Python setup.py for tempregpy package"""
import io
import os
from setuptools import find_packages, setup


HERE = os.path.abspath(os.path.dirname(__file__))

# FINAL_RELEASE is the last stable version of TempRegPy
# A more precisely version try to be automatically determined from the git repository using setuptools_scm.
# If it's not possible (using git archive tarballs for example), FINAL_RELEASE will be used as fallback version.
# edited manually when a new release is out (git tag -a)
FINAL_RELEASE = open(os.path.join(HERE, 'VERSION')).read().strip()

def read(*paths, **kwargs):
    """Read the contents of a text file safely."""
    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content

def read_requirements(path):
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]

setup(
    name="tempregpy",
    use_scm_version={
        'version_scheme': 'post-release',
        'local_scheme': lambda version: version.format_choice("" if version.exact else "+{node}", "+dirty"),
        'fallback_version': FINAL_RELEASE,
    },
    setup_requires=['setuptools_scm'],
    description="Awesome tempregpy created by energy-modelling-hub",
    url="https://github.com/energy-modelling-hub/TempRegPy/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="M. Pavičević, Q. Ploussard",
    packages=find_packages(exclude=["tests", ".github"]),
    license="MIT License",
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": ["tempregpy = tempregpy.__main__:main"]
    },
    # extras_require={"test": read_requirements("requirements-test.txt")},
)
