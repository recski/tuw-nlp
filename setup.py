import os
import subprocess

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.egg_info import egg_info


class SetupAltoDevelop(develop):
    def run(self):
        develop.run(self)
        os.system("echo 'Setting up Alto parser'")
        os.system(f"bash {os.getcwd()}/setup.sh")

        if os.environ.get('ALTO_JAR') is None:
            with open(os.path.expanduser("~/.bashrc"), "a") as outfile:
                outfile.write(f"export ALTO_JAR={os.getcwd()}/alto-2.3.6-SNAPSHOT-all.jar")
                os.system('bash -c \'source ~/.bashrc\'')

class SetupAltoInstall(install):
    def run(self):
        install.run(self)
        os.system("echo 'Setting up Alto parser'")
        os.system(f"bash {os.getcwd()}/setup.sh")

        if os.environ.get('ALTO_JAR') is None:
            with open(os.path.expanduser("~/.bashrc"), "a") as outfile:
                outfile.write(f"export ALTO_JAR={os.getcwd()}/alto-2.3.6-SNAPSHOT-all.jar")
                os.system('bash -c \'source ~/.bashrc\'')

class SetupAltoEgg(egg_info):
    def run(self):
        egg_info.run(self)
        os.system("echo 'Setting up Alto parser'")
        os.system(f"bash {os.getcwd()}/setup.sh")

        if os.environ.get('ALTO_JAR') is None:
            with open(os.path.expanduser("~/.bashrc"), "a") as outfile:
                outfile.write(f"export ALTO_JAR={os.getcwd()}/alto-2.3.6-SNAPSHOT-all.jar")
                os.system('bash -c \'source ~/.bashrc\'')

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
        'stanza',
        'nltk'
    ],
    packages=find_packages(),
    scripts=['setup.sh'],
    cmdclass={'develop': SetupAltoDevelop, 'install': SetupAltoInstall, "egg_info": SetupAltoEgg},
    zip_safe=False)
