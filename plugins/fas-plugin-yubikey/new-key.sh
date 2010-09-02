#!/bin/bash
set -e
cd /tmp
echo "Passed $1" >&2
echo -n $(/srv/dev/fas/plugins/fas-plugin-yubikey/gen_yubikey.py $1 | /usr/bin/ykksm-import --verbose --database 'DBI:Pg:dbname=ykksm;host=localhost' --db-user ykksmimporter --db-passwd uTi2oabe | /usr/bin/awk -F, '/line/{ print $2,$3,$4 }')
#echo -n $(/usr/bin/ykksm-gen-keys --urandom $1 $1 | /usr/bin/gpg --homedir=/srv/dev/gpg -a --encrypt -r 5ADA7BBA -s | /usr/bin/ykksm-import --verbose --database 'DBI:Pg:dbname=ykksm;host=localhost' --db-user ykksmimporter --db-passwd uTi2oabe | /usr/bin/awk -F, '/line/{ print $2,$3,$4 }')
