"""Setup for mgz_hd — AoE2 HD replay parser."""
from setuptools import setup, find_packages

setup(
    name='mgz_hd',
    version='1.8.27',
    description='Parse Age of Empires 2 HD recorded games.',
    url='https://github.com/Emaren/mgz_hd',  # updated to reflect your fork
    license='MIT',
    author='Emaren (forked from happyleaves)',
    author_email='your.email@example.com',  # optional, update as needed
    packages=find_packages(),
    install_requires=[
        'aocref>=2.0.20',
        'construct==2.8.16',
        'dataclasses==0.8; python_version < "3.7"',
        'tabulate>=0.9.0',
    ],
    entry_points={
        'console_scripts': ['mgz_hd=mgz_hd.cli:main'],  # renamed for clarity
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.6',
)
