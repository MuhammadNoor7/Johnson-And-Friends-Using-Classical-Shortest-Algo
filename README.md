# i232520-MuhammadNoor-Algo-Asst3
# Compact README — single-file submission for Assignment 3 (shortest-path algorithms).

# Files
-`i232520-MuhammadNoor-Algo-Asst3.py` — implementation and CLI (`run` / `experiment`).
-`inputs.txt` — sample input (place next to the script or in the parent folder).
-`run_code.bat` — convenience batch (runs under `cmd.exe`).

# Requirements
-csv(For tables)

# Quick run
Place`i232520-MuhammadNoor-Algo-Asst3.py` and`inputs.txt` together and run:

```cmd
python i232520-MuhammadNoor-Algo-Asst3.py run --input inputs.txt --algorithm Dijkstra --source 1
python i232520-MuhammadNoor-Algo-Asst3.py run --input inputs\sample.txt --algorithm Dijkstra --source 1

From inside inputs_folder,
python ..\i232520-MuhammadNoor-Algo-Asst3.py run --input sample.txt --algorithm Dijkstra --source 1

```
You can also run the experiment harness to generate performance CSVs. Example:

```cmd
python i232520-MuhammadNoor-Algo-Asst3.py experiment --output algos_exp_analysis.csv --graph-types Sparse --sizes 10 30 50
```
To run the bundled batch from `cmd.exe`:

```cmd
.\run_code.bat
```
From PowerShell you can also run the batch with:

```powershell
.\run_code.bat
```
## Notes
- Inputs and command-line `--source` are 1-indexed.
- Dijkstra will abort on graphs with negative-weight edges; use Bellman-Ford for single-source with negatives.
- Experiments export CSV (`algos_exp_analysis.csv`) by default. There is no required external Excel package for the CSV output.

## Tips
- If you see an error about `--algorithm` choices, pass the algorithm name case-insensitively (e.g. `dijkstra` or `Dijkstra`) — the CLI normalizes inputs.
