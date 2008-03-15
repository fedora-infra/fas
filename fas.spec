%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           fas
Version:        0.4
Release:        1%{?dist}
Summary:        Fedora Account System

Group:          Development/Languages
License:        GPLv2
URL:            https://fedorahosted.org/fas2/
Source0:        https://fedorahosted.org/releases/f/e/fedora-infrastructure/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools-devel
BuildRequires:  TurboGears
Requires: TurboGears >= 1.0.4
Requires: python-sqlalchemy >= 0.4
Requires: python-TurboMail
Requires: python-fedora-infrastructure >= 0.2.99.2
Requires: babel
Requires: pygpgme
Requires: python-babel
Requires: python-genshi
Requires: pytz

%description
The Fedora Account System is a web application that manages the accounts of
Fedora Project Contributors.  It's built in TurboGears and comes with a json
API for querying against remotely.

The python-fedora-infrastructure package has a TurboGears identity provider
that works with the Account System.

%package clients
Summary: Clients for the Fedora Account System
Group: Applications/System
Requires: python-fedora
Requires: rhpl

%description clients
Additional scripts that work as clients to the accounts system.

%prep
%setup -q


%build
%{__python} setup.py build --install-data='%{_datadir}/fas'

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --install-data='%{_datadir}/fas' --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
mv $RPM_BUILD_ROOT%{_bindir}/start-fas $RPM_BUILD_ROOT%{_sbindir}
# Unreadable by others because it's going to contain a database password.
install fas.cfg $RPM_BUILD_ROOT%{_sysconfdir}
install client/fas.conf $RPM_BUILD_ROOT%{_sysconfdir}
 
%clean
rm -rf $RPM_BUILD_ROOT

%pre
/usr/sbin/groupadd -r fas &>/dev/null || :
/usr/sbin/useradd  -r -s /sbin/nologin -d /usr/share/fas -M \
                               -c 'Fedora Acocunt System user' -g fas fas &>/dev/null || :



%files
%defattr(-,root,root,-)
%doc README TODO COPYING fas2.sql
%{python_sitelib}/*
%{_datadir}/fas/
%{_sbindir}/start-fas
%attr(0640,root,apache) %config(noreplace) %{_sysconfdir}/fas.cfg

%files clients
%{_bindir}/*
%config(noreplace) %{_sysconfdir}/fas.conf

%changelog
* Tue Mar 11 2008 Mike McGrath <mmcgrath@redhat.com> - 0.4-1
- added fas.conf will fix later.

* Mon Mar 10 2008 Mike McGrath <mmcgrath@redhat.com> - 0.3-1
- Upstream released a new version.

* Mon Mar 10 2008 Mike McGrath <mmcgrath@redhat.com> - 0.2-1
- Added fas user/group

* Mon Mar 10 2008 Toshio Kuratomi <tkuratom@redhat.com> - 0.1-1
- Initial Build.
