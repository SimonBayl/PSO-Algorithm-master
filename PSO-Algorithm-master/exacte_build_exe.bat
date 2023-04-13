if exist "build" rd /s /q "build"
if exist "exacte_exe" rd /s /q "exacte_exe"
py -3 -m pipenv run pyinstaller --distpath .\exacte_exe -y --clean -F exacte.py
if not exist "exacte_exe\CPLEX" mkdir "exacte_exe\CPLEX"
copy /b/v/y "CPLEX\Exacte.mod" "exacte_exe\CPLEX\Exacte.mod"
pause