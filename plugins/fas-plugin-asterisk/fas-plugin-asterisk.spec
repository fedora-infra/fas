%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           fas-plugin-asterisk
Version:        0.6
Release:        1%{?dist}
Summary:        Asterisk plugin for FAS2

Group:          Development/Languages
License:        GPLv2
URL:            https://fedorahosted.org/fas/
Source0:        fas-plugin-asterisk-%{version}.tar.gz
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildArch:      noarch
BuildRequires:  python-devel TurboGears
%if 0%{?fedora} >= 8
BuildRequires:  python-setuptools-devel
%else
BuildRequires:  python-setuptools
%endif
#BuildRequires:  fas
Requires:       fas >= 0.8.4.2

%description
Asterisk plugin for FAS2

%prep
%setup -q


%build
%{__python} setup.py build


%install
%{__rm} -rf %{buildroot}
%{__python} setup.py install --skip-build --root %{buildroot}

 
%clean
%{__rm} -rf %{buildroot}


%files
%defattr(-,root,root,-)
#%doc docs/*
%{python_sitelib}/fas_asterisk
%{python_sitelib}/*.egg-info


%changelog
* Mon Feb 16 2009 Ricky Zhou <ricky@fedoraproject.org> -0.6-1
- Allow systems users to get this info.

* Mon Feb 16 2009 Ricky Zhou <ricky@fedoraproject.org> -0.5-1
- Actually fix PIN security issue.

* Mon Feb 16 2009 Ricky Zhou <ricky@fedoraproject.org> -0.4-1
- Fix PIN security issue.

* Mon Jun 16 2008 Ricky Zhou <ricky@fedoraproject.org> -0.3-1
- Bugfix.

* Mon Jun 16 2008 Mike McGrath <mmcgrath@redhat.com> -0.2-1
- Upstream released version
- Renamed package name
- Added TurboGears as a build req

* Mon Jun 16 2008 Ricky Zhou <ricky@fedoraproject.org> - 0.1-1
- Initial RPM Package.
