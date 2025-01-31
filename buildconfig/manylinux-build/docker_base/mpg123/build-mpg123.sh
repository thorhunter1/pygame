#!/bin/bash
set -e -x

MPG123="mpg123-1.28.2"

cd $(dirname `readlink -f "$0"`)

curl -sL https://downloads.sourceforge.net/sourceforge/mpg123/${MPG123}.tar.bz2 > ${MPG123}.tar.bz2
sha512sum -c mpg123.sha512

bzip2 -d ${MPG123}.tar.bz2
tar xf ${MPG123}.tar
cd $MPG123
./configure --enable-int-quality --disable-debug
make
make install
cd ..
