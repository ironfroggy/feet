import setuptools

with open("README.md", "r", encoding='utf8') as f:
    long_description = f.read()

setuptools.setup(
    name="feet",
    version=open("VERSION.txt").read(),
    author="Calvin Spealman",
    author_email="ironfroggy@gmail.com",
    description="Feet makes Python run",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ironfroggy/feet",
    modules=['feetmaker'],
    entry_points = {
        'console_scripts': [
            'mkfeet=feetmaker:main',
        ],
    },
    install_requires=[
        'requirements-parser',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Windows",
    ],
)