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
    cmake -G "Visual Studio 14 2015 Win64" -DMAYA_VERSION=%1 ../
) ELSE (
    cmake -G "Visual Studio 15 2017 Win64" -DMAYA_VERSION=%1 ../
)
cmake --build . --target install --config Release
cd ..
goto :eof
