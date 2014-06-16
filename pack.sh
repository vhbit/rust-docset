#!/bin/sh

SOURCE_DIR="$1"
OUT_DIR="$2"
DOCSET_NAME="RustNightly.docset"
DOCSET_TGZ="RustNightly.tgz"

rm -rf $OUT_DIR
mkdir -p $OUT_DIR

echo "Creating docset"
./indexer.py $SOURCE_DIR $OUT_DIR

echo "Copying feed XML"
cp RustNightly.xml $OUT_DIR

echo "Packing"
cd $OUT_DIR
tar --exclude='.DS_Store' -czf $DOCSET_TGZ $DOCSET_NAME

echo "Metadata"
HASH=`openssl sha1 $DOCSET_TGZ | cut -d " " -f 2`
DT=`date +%Y-%m-%d-%H-%M`
cat ../RustNightly.xml | sed "s/__DT__/$DT/g;s/__SHA__/$HASH/g" > RustNightly.xml

# dash-feed://https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fnet.vhbit.rust-doc%2FRustNightly.xml

# pages with refresh
