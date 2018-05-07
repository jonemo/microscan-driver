from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='microscan',
    version='0.0.2',
    packages=find_packages(where='src'),
    package_dir={"": "src"},
    install_requires=['pyserial'],

    entry_points={
        'console_scripts': [
            'microscan_server=microscan.tools.server:main',
        ],
    },

    description='Python driver from Microscan barcode readers',
    long_description=long_description,
    url='https://github.com/jonemo/microscan-driver',
    author='Jonas Neubert',
    author_email='jn@jonasneubert.com',
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Hardware :: Hardware Drivers',
    ],
)
