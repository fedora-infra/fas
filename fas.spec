%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           fas
Version:        0.8.1
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
BuildRequires:  gettext
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
%{__python} setup.py build --install-data='%{_datadir}'


%install
%{__rm} -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --install-data='%{_datadir}' --root %{buildroot}
%{__mkdir_p} %{buildroot}%{_sbindir}
%{__mkdir_p} %{buildroot}%{_sysconfdir}
%{__mv} %{buildroot}%{_bindir}/start-fas %{buildroot}%{_sbindir}
# Unreadable by others because it's going to contain a database password.
%{__install} -m 640 fas.cfg %{buildroot}%{_sysconfdir}
%{__install} -m 600 client/fas.conf %{buildroot}%{_sysconfdir}
%find_lang %{name}

%clean
%{__rm} -rf %{buildroot}


%pre
/usr/sbin/useradd -c 'Fedora Acocunt System user' -s /sbin/nologin \
    -r -M -d %{_datadir}fas fas &> /dev/null || :


%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README TODO COPYING fas2.sql
%{python_sitelib}/*
%{_datadir}/fas/
%{_sbindir}/start-fas
%attr(-,root,fas) %config(noreplace) %{_sysconfdir}/fas.cfg

%files clients
%{_bindir}/*
%config(noreplace) %{_sysconfdir}/fas.conf

%changelog
* Tue Mar 14 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8.1-1
- Upstream released a new version

* Tue Mar 14 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8-1
- Upstream released a new version

* Tue Mar 13 2008 Mike McGrath <mmcgrath@redhat.com> - 0.7.1-1
- Upstream released new version

* Tue Mar 13 2008 Mike McGrath <mmcgrath@redhat.com> - 0.7-1
- Upstream released new version

* Tue Mar 13 2008 Mike McGrath <mmcgrath@redhat.com> - 0.6-1
- Upstream released a new version

* Tue Mar 11 2008 Mike McGrath <mmcgrath@redhat.com> - 0.5-1
- Upstream released a new version

* Tue Mar 11 2008 Mike McGrath <mmcgrath@redhat.com> - 0.4-1
- added fas.conf will fix later.

* Mon Mar 10 2008 Mike McGrath <mmcgrath@redhat.com> - 0.3-1
- Upstream released a new version.

* Mon Mar 10 2008 Mike McGrath <mmcgrath@redhat.com> - 0.2-1
- Added fas user/group

* Mon Mar 10 2008 Toshio Kuratomi <tkuratom@redhat.com> - 0.1-1
- Initial Build.
