echo off
cls
echo A schonherz-matrix\vlc\plugins.zip fajlt csomagold ki schonherz-matrix\plugins\ mappava konvertalas elott!
pyinstaller.exe -w -F -i icon.ico --onedir editor.pyw
xcopy "vlc\libvlc.dll" "dist\editor\"
xcopy "vlc\libvlccore.dll" "dist\editor\"
xcopy /s /i "images" "dist\editor\images\"
xcopy /s /i "plugins" "dist\editor\plugins\"
pause