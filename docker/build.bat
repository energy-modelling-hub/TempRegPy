python -m venv env
call .\env\scripts\activate.bat
python -m pip install -r requirements2.txt
python -m pip install tqdm
pyinstaller RunWAPASim.spec