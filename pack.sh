#!/bin/sh

SOURCE_DIR="$1"
DOCSET_DIR="$2/RustNightly.docset"
CONTENT_DIR="$DOCSET_DIR/Contents"
DOC_DIR="$DOCSET_DIR/Contents/Resources/Documents"
IDX_DIR="$DOCSET_DIR/Contents/Resources"
mkdir -p $DOC_DIR && cp -R $SOURCE_DIR/ $DOC_DIR && cp Info.plist $CONTENT_DIR/ && (find $DOC_DIR -type f -name \*.html | ./indexer.py $DOC_DIR $IDX_DIR)