"""
Setup configuration for Orbital Defense game.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="orbital-defense",
    version="0.1.0",
    author="Physics Game Developer",
    description="A physics-based CLI space shooter game",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/orbital-defense",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: Arcade",
        "Topic :: Education :: Physics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pytest>=7.0.0",
        "pyyaml>=6.0.0",
        "pandas>=1.3.0",
        "rich>=10.0.0",
        "keyboard>=0.13.5"
    ],
    entry_points={
        "console_scripts": [
            "orbital-defense=orbital_defense.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "orbital_defense": ["config/*.yaml"],
    },
) 