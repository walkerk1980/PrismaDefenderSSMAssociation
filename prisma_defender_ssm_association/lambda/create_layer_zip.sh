cd dependency_layer

# Pre creation cleanup
rm -fvr "${OLDPWD}/dependency_layer.zip"
rm -fvr .venv python && mkdir python/

# pull packages and create zip
python3 -m venv .venv
source .venv/bin/activate && pip install -r requirements.txt && deactivate
cp -fvr .venv/lib/python3.8/site-packages/. ./python
zip -r9 "${OLDPWD}/dependency_layer.zip" python

# Post cleanup
rm -fvr .venv python