# Run Extras repoclosure against EPEL 5.

# i386
#./rc-modified -q -d mdcache -n -c yum.epel.conf -a i686 -r centos-5-i386 -r centos-updates-5-i386 -r fedora-epel-5-i386 -r fedora-epel-testing-5-i386 > rc-epel5-20080113.txt

# x86_64 : APPEND!
#./rc-modified -q -d mdcache -n -c yum.epel.conf -a x86_64 -r centos-5-x86_64 -r centos-updates-5-x86_64 -r fedora-epel-5-x86_64 -r fedora-epel-testing-5-x86_64 >> rc-epel5-20080113.txt

# Show summary which can be sent to mailing-list.
./rc-report.py rc-epel5-20080113.txt -k epel -c rc-report-epel.cfg -w testing
