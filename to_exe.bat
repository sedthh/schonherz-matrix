echo off
cls
echo A plugins.zip fajlt csomagold ki plugins\ mappava konvertalas elott!
pyinstaller.exe -w -F -i icon.ico --onedir --hidden-import=libvlccore.dll editor.pyw
xcopy libvlc.dll "dist\editor\"
xcopy /s /i "images" "dist\editor\images\"
xcopy /s /i "plugins" "dist\editor\plugins\"
pause