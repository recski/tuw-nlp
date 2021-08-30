import os
import subprocess
import sys

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.egg_info import egg_info


class SetupAltoDevelop(develop):
    def run(self):
        develop.run(self)
        os.system("echo 'Setting up Alto parser'")
        run_script_install()


class SetupAltoInstall(install):
    def run(self):
        install.run(self)
        os.system("echo 'Setting up Alto parser'")
        run_script_install()


class SetupAltoEgg(egg_info):
    def run(self):
        egg_info.run(self)
        os.system("echo 'Setting up Alto parser'")
        run_script_install()


def run_script_install():
    if os.name == 'nt':  # use ps1 script
        os.system(
            f'powershell iex -Command "$( get-content {os.getcwd()}/setup.ps1 | Out-String )"')
    else:
        os.system(f"bash {os.getcwd()}/setup.sh")


setup(
    name='tuw-nlp',
    version='0.1',
    description='NLP tools at TUW Informatics',
    url='http://github.com/recski/tuw-nlp',
    author='Gabor Recski,Adam Kovacs',
    author_email='gabor.recski@tuwien.ac.at,adam.kovacs@tuwien.ac.at',
    license='MIT',
    install_requires=[
        'dict-recursive-update',
        'networkx',
        'penman',
        'stanza==1.1.1',
        'nltk',
        "graphviz"
    ],
    packages=find_packages(),
    scripts=['setup.sh'],
    include_package_data=True,
    cmdclass={'develop': SetupAltoDevelop,
              'install': SetupAltoInstall, "egg_info": SetupAltoEgg},
    zip_safe=False)
