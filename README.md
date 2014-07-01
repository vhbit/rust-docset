rust-docset
=============

It started as Dash docset generator for Rust documentation but became
quite flexible, so other languages/html types could be added
relatively easily. There are 3 kinds of rules:

- File rules which describe how to process a file based on its name

- Index rules which describe which data and how should be scraped from
  HTML docs to index using xpath selectors

- TOC rules which describe how to inject corresponding TOC anchors
again based on xpath selectors.

Providing a new backend should be (ohh, at least I think so) as simple
as creating new rules and binding them all together.

There is no more documentation on it yet other than sources from in
`docset/rust`.

Installation
============

    git clone https://github.com/vhbit/rust-docset.git
    cd rust-docset
    virtualenv create .venv
    source .venv/bin/activate
    pip install -r requirements.txt


Usage
=====


Generating docset for a Rust crate
------------

    invoke build

There are 3 additional arguments:

- doc dir (`-d` or `--doc_dir`)

- output dir (`-o` or `--out_dir`)

- configuration file (`-c` or `--conf`)

It searches for a file `docset.toml` and uses it as
configuration. Arguments passed through command line always ovveride
those provided in configuration file. Configuration description is below.

Nightly
--------

There is a built-in configuration for Rust Nightly and also a special
command:

    invoke update_nightly

Last processed version is remembered to avoid redundant updates, but
that could be skipped by using force update:

    invoke update_nightly -f

or

    invoke update_nightly --force


Configuration sample
============================

Here is a sample file:

    [docset]
    name = "LMDB"
    bundle_id = "lmdb-rs"
    version = "0.3"
    type = "docset.rust"
    doc_dir = "doc"
    out_dir = "lmdb_doc_out"

    [feed]
    base_url = "http://somewhere.doc"
    upload_cmd = "upload.sh"

You can also check `nighly.toml`

Configuration description
===================================

Relative paths
-----------

if path is not absolute it is considered to be relative to
the directory with config file. I.e. if config file is located in
`/home/vhbit/projects/lmdb/docset.toml` when value
`template/info.plist` will turn into
`/home/vhbit/projects/lmdb/template/info.plist`.


Docset
-------
- `name` specifies docset name

- `bundle_id`, required, should be an unique identifier, preferrable
in form of net.vhbit.lmdb-rs

- `version`, semi-optional, specifies version of crate. Note, that version
  should be bumped with package version bumps. Dash still provides a
  way to update docsets within a version (for example, if there was a
  small glitch which was fixed). It defaults to "0.1" if not specified

- `type`, required, defines which rules will be used for docset
  generation. Predefined values so far are `docset.rust` for Rust
  crate and `docset.rust:nightly` for generating Rust documentation
  itself

- `plist`, optional, specifies path to Info.plist if you ever need to
  use a different template. For example of template you can check
  `docset/rust/templates.py`.

- `icon`, optional, specifies path to icon for docset

- `doc_dir`, semi-optional, specifies path to process for generating
  docset. For Rust projects it should be path to `doc`
  directory. Defaults to current directory. Although it is optional,
  there will be a warning if it is not specified in `docset.toml` or
  as command line arg as it is prefferable to have an explicitly
  described path. Note also that command line arguments take
  precedence over contents of config file

- `out_dir`, semi-optional, specifies path there docset output will be
  placed. Defaults to ds_out. _WARNING!_ This directory will be
  deleted before every build. Warnings and precendence is the
  same as for `doc_dir`

Feed
----
- `base_url`, required, specifies URL to be used in generated feed xml

- `template`, optional, specifies a path to feed xml template if any
  customizations are required. For example of template you can check
  `docset/rust/templates.py`

- `upload_cmd`, optional, if present corresponding cmd will be
  launched after generation with 2 arguments: full path to .tgz file
  and full path to feed xml path, for example if
  `upload_cmd = "upload.sh"` after generating docset the following
  command will be executed.

  `upload.sh /Users/vhbit/projects/rust-docset/lmdb/ds_out/lmdb-c6c72217.tgz /Users/vhbit/projects/rust-docset/lmdb/ds_out/lmdb.xml`

  This way it provides enough flexibility in choosing hosting for
  docset although in future it might have a couple of predefined
  deployment options like S3, Github Releases and so on.


Extending for other languages/doc types
=======================================

Documentation yet to be written
