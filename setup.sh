cd "/Users/aditikhandelia/Desktop/IITK ACADS/sem 8/CS335/project/code/Chiron-Framework/ChironCore"
deactivate 2>/dev/null
rm -rf .venv

# find the installed Python.org version folder (e.g., 3.11, 3.12, etc.)
ls /Library/Frameworks/Python.framework/Versions/

# pick the version you see from the ls output (example assumes 3.11)
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -c "import tkinter; print('tk ok')"

# make venv using that Python
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m venv .venv
source .venv/bin/activate

# install deps inside venv
python -m pip install -U pip
python -m pip install antlr4-python3-runtime==4.13.2 networkx numpy
python -m pip install --only-binary=:all: "z3-solver==4.13.2.0"

# run
python chiron.py -r ./example/example1.tl -d '{":x": 20, "y": 30, ":z": 20, ":p": 40}'