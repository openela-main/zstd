# enable .lz4 support by default
%bcond_without lz4

# enable .xz/.lzma support by default
%bcond_without lzma

# enable .gz support by default
%bcond_without zlib

%if 0%{?rhel} && 0%{?rhel} <= 6
# gcc-4.4 is currently too old to compile pzstd
%bcond_with pzstd
%else
%ifarch %{ix86} x86_64
%bcond_without pzstd
%else
# aarch64 and armv7hl at least currently segfault
# in ThreadPool test for the pzstd util
%bcond_with pzstd
%endif
%endif

%ifarch x86_64
%bcond_without asm
%else
# Disable asm to ensure non excutable stack
# used on archs where asm not actually used
# https://github.com/facebook/zstd/issues/2963
%bcond_with asm
%endif

# Disable gtest
%bcond_with gtest

Name:           zstd
Version:        1.5.1
Release:        2%{?dist}
Summary:        Zstd compression library

License:        BSD and GPLv2
URL:            https://github.com/facebook/zstd
Source0:        https://github.com/facebook/zstd/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

Patch1:         pzstd.1.patch
Patch2:         enable-CET.patch

BuildRequires:  make
BuildRequires:  gcc
%if %{with gtest}
BuildRequires:  gtest-devel
%endif
%if %{with lz4}
BuildRequires:  lz4-devel
%endif
%if %{with lzma}
BuildRequires:  xz-devel
%endif
%if %{with pzstd}
BuildRequires:  gcc-c++
%endif
%if %{with zlib}
BuildRequires:  zlib-devel
%endif
BuildRequires:  execstack

%description
Zstd, short for Zstandard, is a fast lossless compression algorithm,
targeting real-time compression scenarios at zlib-level compression ratio.

%package -n lib%{name}
Summary:        Zstd shared library

%description -n lib%{name}
Zstandard compression shared library.

%package -n lib%{name}-devel
Summary:        Header files for Zstd library
Requires:       lib%{name}%{?_isa} = %{version}-%{release}

%package -n lib%{name}-static
Summary:        Static variant of the Zstd library
Requires:       lib%{name}-devel = %{version}-%{release}

%description -n lib%{name}-devel
Header files for Zstd library.

%description -n lib%{name}-static
Static variant of the Zstd library.

%prep
%setup -q
find -name .gitignore -delete
%if %{with pzstd}
%patch1 -p1
%endif
%patch2 -p1

%build
export CFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"
export PREFIX="%{_prefix}"
export LIBDIR="%{_libdir}"
%make_build -C lib lib-mt %{!?with_asm:ZSTD_NO_ASM=1}
%make_build -C programs %{!?with_asm:ZSTD_NO_ASM=1}
%if %{with pzstd}
export CXXFLAGS="$RPM_OPT_FLAGS"
%make_build -C contrib/pzstd %{!?with_asm:ZSTD_NO_ASM=1}
%endif

%check
execstack lib/libzstd.so.1

export CFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"
make -C tests test-zstd
%if %{with pzstd}
%if %{with gtest}
export CXXFLAGS="$RPM_OPT_FLAGS"
make -C contrib/pzstd test
%endif
%endif

%install
%make_install PREFIX=%{_prefix} LIBDIR=%{_libdir}
%if %{with pzstd}
install -D -m755 contrib/pzstd/pzstd %{buildroot}%{_bindir}/pzstd
install -D -m644 programs/%{name}.1 %{buildroot}%{_mandir}/man1/p%{name}.1
%endif

%files
%doc CHANGELOG README.md
%{_bindir}/%{name}
%if %{with pzstd}
%{_bindir}/p%{name}
%{_mandir}/man1/p%{name}.1*
%endif
%{_bindir}/%{name}mt
%{_bindir}/un%{name}
%{_bindir}/%{name}cat
%{_bindir}/%{name}grep
%{_bindir}/%{name}less
%{_mandir}/man1/%{name}.1*
%{_mandir}/man1/un%{name}.1*
%{_mandir}/man1/%{name}cat.1*
%{_mandir}/man1/%{name}grep.1*
%{_mandir}/man1/%{name}less.1*
%license COPYING LICENSE

%files -n lib%{name}
%{_libdir}/libzstd.so.*
%license COPYING LICENSE

%files -n lib%{name}-devel
%{_includedir}/zdict.h
%{_includedir}/zstd.h
%{_includedir}/zstd_errors.h
%{_libdir}/pkgconfig/libzstd.pc
%{_libdir}/libzstd.so

%files -n lib%{name}-static
%{_libdir}/libzstd.a

%ldconfig_scriptlets -n lib%{name}

%changelog
* Mon Feb 07 2022 Jakub Martisko <jamartis@redhat.com> - 1.5.1-2
- Add some basic gating tests
  Resolves: rhbz#2050272

* Wed Jan 12 2022 Michel Alexandre Salim <salimma@centosproject.org> - 1.5.1-1
- Rebase to the latest upstream version
- Enable optional gz, xz/lzma, and lz4 support in the zstd tool
- Disable amd64 assembly on non-x86_64 architectures (rhbz#2035802)
  this should avoid the issue where an executable stack is created
- Re-enable CET protections (rhbz#2039353)
  Resolves: rhbz#2039488

* Tue Aug 10 2021 Mohan Boddu <mboddu@redhat.com> - 1.5.0-2
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Mon Jul 12 2021 Jakub Martisko <jamartis@redhat.com> - 1.5.0-1
* Rebase to the latest upstream version
Resolves: rhbz#1928094

* Thu Jul 01 2021 Jakub Martisko <jamartis@redhat.com> - 1.4.9-3
- Drop gtest-devel dependency
Resolves: rhbz#1977606

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 1.4.9-2
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Fri Mar 05 2021 Pádraig Brady <P@draigBrady.com> - 1.4.9-1
- Latest upstream

* Thu Jan 28 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Thu Dec 17 2020 Pádraig Brady <P@draigBrady.com> - 1.4.7-1
- Latest upstream

* Wed Aug 26 2020 Jeff Law <law@redhat.com> - 1.4.5-6
- Do not force C++11 mode

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.5-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Sat Jul 11 2020 Igor Raits <ignatenkobrain@fedoraproject.org> - 1.4.5-4
- Build libzstd with multi-threading support

* Mon May 25 2020 Pádraig Brady <P@draigBrady.com> - 1.4.5-3
- Build shared library with correct compiler flags

* Fri May 22 2020 Pádraig Brady <P@draigBrady.com> - 1.4.5-1
- Latest upstream

* Fri May 22 2020 Avi Kivity <avi@scylladb.com> - 1.4.4-3
- Added static library subpackage

* Fri Jan 31 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Wed Jan 15 2020 Pádraig Brady <P@draigBrady.com> - 1.4.4-1
- Latest upstream

* Wed Jul 31 2019 Pádraig Brady <P@draigBrady.com> - 1.4.2-1
- Latest upstream

* Sat Jul 27 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Mon Apr 29 2019 Pádraig Brady <P@draigBrady.com> - 1.4.0-1
- Latest upstream

* Sun Feb 03 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Mon Dec 31 2018 Pádraig Brady <P@draigBrady.com> - 1.3.8-1
- Latest upstream

* Mon Oct 08 2018 Pádraig Brady <P@draigBrady.com> - 1.3.6-1
- Latest upstream

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Mon Jul 02 2018 Pádraig Brady <P@draigBrady.com> - 1.3.5.1
- Latest upstream

* Wed Mar 28 2018 Pádraig Brady <P@draigBrady.com> - 1.3.4-1
- Latest upstream

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Feb 02 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1.3.3-2
- Switch to %%ldconfig_scriptlets

* Thu Dec 21 2017 Pádraig Brady <P@draigBrady.com> - 1.3.3-1
- Latest upstream

* Fri Nov 10 2017 Pádraig Brady <P@draigBrady.com> - 1.3.2-1
- Latest upstream

* Mon Aug 21 2017 Pádraig Brady <P@draigBrady.com> - 1.3.1-1
- Latest upstream

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sun Jul 16 2017 Pádraig Brady <P@draigBrady.com> - 1.3.0-1
- Latest upstream

* Mon May 08 2017 Pádraig Brady <P@draigBrady.com> - 1.2.0-1
- Latest upstream

* Mon Mar 06 2017 Pádraig Brady <P@draigBrady.com> - 1.1.3-1
- Latest upstream

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Nov 02 2016 Pádraig Brady <pbrady@redhat.com> - 1.1.1-1
- Latest upstream

* Thu Oct 6  2016 Pádraig Brady <pbrady@fb.com> 1.1.0-2
- Add pzstd(1)

* Thu Sep 29 2016 Pádraig Brady <pbrady@fb.com> 1.1.0-1
- New upstream release
- Remove examples and static lib

* Mon Sep 12 2016 Pádraig Brady <pbrady@fb.com> 1.0.0-2
- Adjust various upstream links
- Parameterize various items in spec file

* Mon Sep 5 2016 Pádraig Brady <pbrady@fb.com> 1.0.0-1
- Initial release
