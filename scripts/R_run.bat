Rscript -e '.libPaths()'
set R_USER=C:\R
set R_HOME=C:\R
set PATH=%R_HOME%\bin\i386;%PATH%
set PATH=%R_HOME%\bin;%PATH%
set PATH=%R_HOME%\bin\x64;%PATH%
set PATH=%R_HOME%;%PATH%
echo %PATH%
set
python %1 %2 %3 %4 %5 %6


