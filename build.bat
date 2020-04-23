@echo off
FOR %%G IN (2018, 2019, 2020) DO (call :subroutine "%%G")
GOTO :eof

:subroutine
set builddir=build.%1
if not exist %builddir% goto BUILDENV
del %builddir% /S /Q
:BUILDENV
mkdir %builddir%
cd %builddir%
if %1 LSS "2020" (
    cmake -A x64 -T v140 -DMAYA_VERSION=%1 ../
) ELSE (
    cmake -A x64 -T v141 -DMAYA_VERSION=%1 ../
)
cmake --build . --target install --config Release
cd ..
goto :eof
