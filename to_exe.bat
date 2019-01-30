echo off
cls
pyinstaller.exe -w -F -i icon.ico --onedir editor.pyw
xcopy /s /i "images" "dist\editor\images\"
xcopy /s /i "plugins" "dist\editor\plugins\"
pause