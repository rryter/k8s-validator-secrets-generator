# cli.py
import subprocess
from mnemonic import Mnemonic
import click
import sys
import os
import argparse
import glob


sys.path.append('my/path/to/module/folder')


@click.command()
def main():

    network = 'l15-testnet-dev'
    amountOfNodes = 2
    namespace = "dev"

    os.mkdir(network)
    os.system("kubeseal --fetch-cert --controller-name=sealed-secrets --controller-namespace=sealed-secrets > pub-sealed-secrets.pem -n sealed-secrets")

    for x in range(amountOfNodes):
        print("Generating sealed keys for node " + str(x))
        mnemo = Mnemonic("english")
        words = mnemo.generate(strength=256)

        folder = network +"/node-" + str(x)
        os.mkdir(folder)
        f = open(folder + "/mnemonic", "x")
        try:
            os.system('./lukso-deposit-cli/deposit existing-mnemonic --folder '+ folder +' --num_validators 5 --validator_start_index 5 --keystore_password 12345678 --chain '+network+' --mnemonic "' + words + '" >/dev/null'),
        except subprocess.CalledProcessError as e:
            output = e.output
            print(output)

        commandStart = "kubectl create secret generic validator-keys-node-" + str(x) + " --from-file="
        fromFile = ' --from-file='.join(glob.iglob(folder +'/validator_keys/*.json'))
        commandEnd = " --dry-run=client -o yaml > "+ folder + "/validator-keys-node-" + str(x) + ".yaml -n " + namespace

        os.system(commandStart + fromFile + commandEnd)
        os.system("kubeseal --cert pub-sealed-secrets.pem --format yaml < "+ folder + "/validator-keys-node-" + str(x) + ".yaml > "+ folder + "/validator-keys-node-" + str(x) + "-sealed.yaml -n " + namespace)

if __name__ == "__main__":
    main()
