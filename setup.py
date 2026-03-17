from setuptools import setup, find_packages

setup(
    name="code-translator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "tree-sitter>=0.21.0",
        "tree-sitter-languages>=1.10.0",
    ],
    entry_points={
        "console_scripts": [
            "code-translator=translator.cli:main",
        ],
    },
)
