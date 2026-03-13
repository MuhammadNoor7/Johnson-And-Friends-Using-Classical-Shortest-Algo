@echo off
cd /d "%~dp0"
REM running the assignment script for every test file in inputs
setlocal enabledelayedexpansion
for %%f in ("inputs\*.txt") do (
	echo ==================================================
	echo Running tests for: %%f
	echo ==================================================
	set "FNAME=%%~nxf"
	set "UND="
	REM detecting substring 'undirected' in filename using variable replacement
	if not "!FNAME:undirected=!"=="!FNAME!" (
		set "UND=--undirected"
	)
	python -u "i232520-MuhammadNoor-Algo-Asst3.py" run --input "%%~f" !UND! --algorithm Dijkstra --source 1
	python -u "i232520-MuhammadNoor-Algo-Asst3.py" run --input "%%~f" !UND! --algorithm "Bellman-Ford" --source 1
	python -u "i232520-MuhammadNoor-Algo-Asst3.py" run --input "%%~f" !UND! --algorithm "Floyd-Warshall"
	python -u "i232520-MuhammadNoor-Algo-Asst3.py" run --input "%%~f" !UND! --algorithm Johnson

	echo.
)
endlocal
echo All tests complete.
pause
