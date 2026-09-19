import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bpjs",
    version="0.1.0",

    author="Syamsul",
    author_email="shiday1993@gmail.com",

    description=(
        "Unofficial Python client for BPJS Kesehatan API "
        "supporting VClaim, iCare, Antrean RS, and Aplicare."
    ),

    long_description=long_description,
    long_description_content_type="text/markdown",

    url="https://github.com/shiday1993/bpjs",

    project_urls={
        "Bug Tracker": "https://github.com/shiday1993/bpjs/issues",
        "Source Code": "https://github.com/shiday1993/bpjs",
    },

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.14",
    ],

    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),

    python_requires=">=3.9",

    license="MIT",

    keywords=[
        "bpjs",
        "vclaim",
        "icare",
        "antrean-rs",
        "aplicare",
        "jkn",
    ],

    install_requires=[
        "lzstring",
        "requests",
        "pycryptodome",
    ],
)