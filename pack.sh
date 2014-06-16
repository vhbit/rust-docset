#!/bin/sh

SOURCE_DIR="$1"
OUT_DIR="$2"
DOCSET_NAME="RustNightly.docset"
DOCSET_TGZ="RustNightly.tgz"
DOCSET_DIR="$OUT_DIR/$DOCSET_NAME"
CONTENT_DIR="$DOCSET_DIR/Contents"
DOC_DIR="$DOCSET_DIR/Contents/Resources/Documents"
IDX_DIR="$DOCSET_DIR/Contents/Resources"

rm -rf $DOC_DIR
mkdir -p "$DOC_DIR"
echo "Copying"
cp -R "$SOURCE_DIR/" "$DOC_DIR"
cp Info.plist "$CONTENT_DIR/"
cp icon.png $OUT_DIR/$DOCSET_NAME/
echo "Indexing"
find $DOC_DIR -type f -name \*.html | ./indexer.py $DOC_DIR $IDX_DIR
cp RustNightly.xml $OUT_DIR

echo "Patching CSS"
cat >> $DOC_DIR/main.css <<EOF
/* Dash DocSet overrides */

.sidebar, .sub { display: none; }
.content { margin-left: 0; }
EOF

echo "Packing"
cd $OUT_DIR
tar --exclude='.DS_Store' -czf $DOCSET_TGZ $DOCSET_NAME
echo "Metadata"
HASH=`openssl sha1 $DOCSET_TGZ | cut -d " " -f 2`
DT=`date +%Y-%m-%d`
cat ../RustNightly.xml | sed "s/__DT__/$DT/g;s/__SHA__/$HASH/g" > RustNightly.xml

# dash-feed://https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fnet.vhbit.rust-doc%2FRustNightly.xml

# pages with refresh
