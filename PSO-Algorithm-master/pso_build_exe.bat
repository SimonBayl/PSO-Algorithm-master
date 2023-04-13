if exist "build" rd /s /q "build"
if exist "pso_exe" rd /s /q "pso_exe"
py -3 -m pipenv run pyinstaller --distpath .\pso_exe -y --clean -F pso.py
if not exist "pso_exe\CPLEX" mkdir "pso_exe\CPLEX"
copy /b/v/y "CPLEX\PSO.mod" "pso_exe\CPLEX\PSO.mod"
pause