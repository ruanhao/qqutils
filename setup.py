# setup.py
from setuptools import setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
install_requires = (this_directory / 'requirements.txt').read_text().splitlines()

config = {
    'name': 'qqutils',
    'url': 'https://github.com/ruanhao/qqutils',
    'license': 'MIT',
    "long_description": long_description,
    "long_description_content_type": 'text/markdown',
    'description': 'My collection of useful functions for Python',
    'author' : 'Hao Ruan',
    'author_email': 'ruanhao1116@gmail.com',
    'keywords': ['utils'],
    'version': '0.0.16',
    'packages': ['qqutils'],
    'install_requires': install_requires,
    'python_requires': ">=3.7, <4",
    'setup_requires': ['wheel'],
    'classifiers': [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries",
    ],
}

setup(**config)
