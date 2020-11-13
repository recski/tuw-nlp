from setuptools import find_packages, setup

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
        'stanza'
    ],
    packages=find_packages(),
    zip_safe=False)
