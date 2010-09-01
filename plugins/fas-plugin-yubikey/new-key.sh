#!/bin/bash
set -e

echo -n $(/usr/bin/ykksm-gen-keys --urandom $1 $1 | /usr/bin/gpg -a --encrypt -r DD9259AA -s | /usr/bin/ykksm-import --verbose --database 'DBI:Pg:dbname=ykksm;host=192.168.122.248' --db-user ykksmimporter --db-passwd otherpassword | /usr/bin/awk -F, '/line/{ print $2,$3,$4 }')
