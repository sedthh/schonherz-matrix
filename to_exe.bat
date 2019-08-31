echo off
cls
pyinstaller.exe -w -F -i icon.ico --onedir editor.pyw
xcopy /s /i "images" "dist\editor\images\"
xcopy /s /i "plugins" "dist\editor\plugins\"
xcopy "_libvlc.dll" "dist\editor\libvlc.dll"
xcopy "_libvlccore.dll" "dist\editor\libvlccore.dll"
xcopy "ffmpeg.exe" "dist\editor\ffmpeg.exe"
pause