from setuptools import find_packages, setup

setup(
    name='tc',
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            'tc-repl=tc.__main__:repl',
        ]
    },
)
