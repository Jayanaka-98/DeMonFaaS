* Download Go 1.13 from https://golang.org/dl/

Then after installing run this command or place it in your `$HOME/.bash_profile`

```bash
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
```

* Now clone / build `faas-cli`:

from source run
```bash
mkdir -p $GOPATH/src/github.com/openfaas/
cd $GOPATH/src/github.com/openfaas/
cp -r faas-cli $GOPATH/src/github.com/openfaas/ faas-cli
$ cd $GOPATH/src/github.com/openfaas/faas-cli
$ make local-install
```

* Build multi-arch binaries

To build the release binaries type in:

```
./extract_binaries.sh
```