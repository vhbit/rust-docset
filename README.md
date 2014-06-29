rust-docset
=============

Dash docset generator for Rust documentation.


Installation
============

    git clone
    virtualenv create .venv
    pip install -r requirements.txt

Usage
=====


Generating docset
------------

    invoke build

There are 3 additional arguments:

- doc dir (`-d` or `--doc_dir`)

- output dir (`-o` or `--out_dir`)

- configuration file (`-c` or `--conf`)

It searches for a file `rust-ds.toml` and uses it as
configuration. Arguments passed through command line always ovveride
those provided in configuration file

Configuration file
--------------------

Here is a sample file:

    [docset]
    name = "LMDB" # required
    type = "docset.rust" # required
    plist = "lmdb/info.plist" # required
    icon = "lmdb/icon.png" #optional
    in_dir = "lmdb/doc" #optional
    out_dir = "lmdb_doc_out" #optional, defaults to "doc_out"


Nightly
--------

There is a built-in configuration for nightly and also a special
command:

    invoke update_nightly

Last processed version is remembered to avoid redundant updates, but
that could be skipped by using force update:

    invoke update_nightly -f

or

    invoke update_nightly --force
