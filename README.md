# Usage

- Install Dependencies

```
go get github.com/bitnami-labs/sealed-secrets/cmd/kubeseal@main
pip install --user pipenv
pipenv install
pipenv shell
```

- Create these two password files

```
echo "12345678" >> keys-pw.txt
echo "kNLpePeSY7!GaV" >> password.txt
```

- Edit lines 21 - 24 in [helper/cli.py](helper/cli.py) accordingly

```
python3 helper/cli.py
```

- Happy Dance.
