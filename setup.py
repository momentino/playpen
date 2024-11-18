from setuptools import setup, find_packages

version = "0.1.2"

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="playpen",
    packages=find_packages(),
    version=version,
    license="Apache 2.0",
    description="The Playpen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email="",
    author="The Playpen Consortium",
    install_requires=requirements,
    url="https://github.com/momentino/playpen",
    classifiers=[
        "Intended Audience :: Science/Research",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    include_package_data=True,  # Include non-code files
)