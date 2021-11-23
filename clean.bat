cd .vscode
rename *.json *.save
cd ..

del /s /q bot.spec bot.log source-code.zip windows-installer.exe .\*.json
rmdir /s /q dist\ __pycache__\ build\ cogs\__pycache__

cd .vscode
rename *.save *.json