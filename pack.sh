#!/bin/sh

SOURCE_DIR="$1"
DOCSET_DIR="$2/RustNightly.docset"
CONTENT_DIR="$DOCSET_DIR/Contents"
DOC_DIR="$DOCSET_DIR/Contents/Resources/Documents"
IDX_DIR="$DOCSET_DIR/Contents/Resources"
mkdir -p $DOC_DIR && cp -R $SOURCE_DIR/ $DOC_DIR && cp Info.plist $CONTENT_DIR/ && (find $DOC_DIR -type f -name \*.html | ./indexer.py $DOC_DIR $IDX_DIR)

# tar --exclude='.DS_Store' -cvzf <docset name>.tgz <docset name>.docset
# sha1
# update xml version
# upload to S3 xml + tgz
# check permissions
# dash-feed://https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fnet.vhbit.rust-doc%2FRustNightly.xml