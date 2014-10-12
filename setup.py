from setuptools import setup

setup(name="ddg",
    version="0.1",
    description="Dash Docset Generator",
    author="Valerii Hiora",
    author_email="valerii.hiora@gmail.com",
    license="BSD",
    url="https://github.com/vhbit/rust-docset",
    packages=["docset", "docset.rust"],
    package_data={"docset.rust": ["data/template/*.*", "data/nightly.toml"]},
    install_requires=[        
        "invoke==0.9.0",
        "Jinja2", 
        "lxml",
        "requests",
        "toml"],
    dependency_links=["git+https://github.com/vhbit/invoke.git@task-in-packages#egg=invoke-0.9.0"],
    entry_points={
        'console_scripts': ['ddg = docset.cli:main', 'ddg-rs = docset.rust.cli:main']
    },
    zip_safe=False, 
    classifiers=[
'Development Status :: 3 - Alpha',
'Environment :: Console',
'Intended Audience :: Developers',
'License :: OSI Approved :: BSD License',
'Operating System :: MacOS :: MacOS X',
'Operating System :: Unix',
'Operating System :: POSIX',
'Programming Language :: Python',
'Programming Language :: Python :: 2.6',
'Programming Language :: Python :: 2.7',
'Topic :: Documentation',
'Topic :: Software Development',
'Topic :: Software Development :: Build Tools',
'Topic :: Software Development :: Libraries',
'Topic :: Software Development :: Libraries :: Python Modules',
],)