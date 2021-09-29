# cli.py
from mnemonic import Mnemonic
import click
import sys
import os
import glob


sys.path.append('my/path/to/module/folder')


@click.command()
def main():

    network = 'l15-testnet-dev'
    amountOfNodes = 5
    namespace = "dev"
    depositCli = "https://github.com/lukso-network/network-deposit-cli/releases/download/v1.2.4-l15/lukso-deposit-cli-8cf72bf-linux-amd64.tar.gz"
    depositCliName = depositCli.split('/')[-1]
    os.mkdir(network)
    os.mkdir(network + "/sealed-secrets")

    os.system("wget " + depositCli + " >/dev/null")
    os.system("tar -zxf "+depositCliName + " >/dev/null")
    os.system("mv " + depositCliName.replace(".tar.gz", "") + " lukso-deposit-cli >/dev/null")
    os.system("rm " + depositCliName + " >/dev/null")
    os.system("kubeseal --fetch-cert --controller-name=sealed-secrets --controller-namespace=sealed-secrets > pub-sealed-secrets.pem -n sealed-secrets")

    print("mv " + depositCliName.replace(".tar.gz", "") + " lukso-deposit-cli")
    for x in range(amountOfNodes):
        print("Generating sealed keys for node " + str(x))
        mnemo = Mnemonic("english")
        words = mnemo.generate(strength=256)

        folder = network +"/node-" + str(x)
        os.mkdir(folder)
        f = open(folder + "/mnemonic", "x")
        f.write(words)

        os.system('./lukso-deposit-cli/deposit existing-mnemonic --folder '+ folder +' --num_validators 5 --validator_start_index 5 --keystore_password 12345678 --chain '+network+' --mnemonic "' + words + '" >/dev/null'),

        commandStart = "kubectl create secret generic validator-keys-node-" + str(x) + " --from-file="
        fromFile = ' --from-file='.join(glob.iglob(folder +'/validator_keys/*.json'))
        commandEnd = " --dry-run=client -o yaml > "+ folder + "/validator-keys-node-" + str(x) + ".yaml -n " + namespace

        os.system(commandStart + fromFile + commandEnd)
        os.system("kubeseal --cert pub-sealed-secrets.pem --format yaml < "+ folder + "/validator-keys-node-" + str(x) + ".yaml > "+ network + "/sealed-secrets/validator-keys-node-" + str(x) + "-sealed.yaml -n " + namespace)

if __name__ == "__main__":
    main()
