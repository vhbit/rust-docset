from distutils.core import setup

setup(name="dds",
    version="0.1",
    description="Dash Docset generator",
    author="Valerii Hiora",
    author_email="valerii.hiora@gmail.com",
    url="https://github.com/vhbit/rust-docset",
    packages=["docset", "docset.rust"],
    package_data={"docset.rust": ["data/template/*.*", "data/nightly.toml"]})