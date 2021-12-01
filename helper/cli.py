# cli.py
from mnemonic import Mnemonic
import click
import os
import glob
import json

@click.command()
def main():

    network = 'l15-dev'
    amountOfNodes = 8
    namespace = "dev"
    depositCli = "https://github.com/lukso-network/network-deposit-cli/releases/download/v1.2.6-LUKSO/lukso-deposit-cli-Linux-x86_64"
    depositCliName = depositCli.split('/')[-1]
    os.mkdir(network)
    os.mkdir(network + "/sealed-secrets")

    os.system("wget " + depositCli + " >/dev/null")
    os.system("mv " + depositCliName + " lukso-deposit-cli >/dev/null")
    os.system("chmod +x " + depositCliName + " lukso-deposit-cli >/dev/null")
    os.system("kubeseal --fetch-cert --controller-name=sealed-secrets --controller-namespace=sealed-secrets > pub-sealed-secrets.pem -n sealed-secrets")

    for x in range(amountOfNodes):
        print("Generating sealed keys for node " + str(x))
        mnemo = Mnemonic("english")
        words = mnemo.generate(strength=256)

        folder = network +"/wallet-" + str(x)
        os.mkdir(folder)
        f = open(folder + "/mnemonic", "x")
        f.write(words)

        os.system('./lukso-deposit-cli existing-mnemonic --folder '+ folder +' --num_validators 10 --validator_start_index 0 --keystore_password 12345678 --chain '+network+' --mnemonic "' + words + '" >/dev/null'),

        createWallets(network, str(x))

        commandStart = "kubectl create secret generic validator-keys-node-" + str(x)
        fromFile = ' --from-file='+folder +'/wallet/direct/accounts/all-accounts.keystore.json'
        commandEnd = " --dry-run=client -o yaml > "+ folder + "/validator-keys-node-" + str(x) + ".yaml -n " + namespace

        os.system(commandStart + fromFile + commandEnd)
        os.system("kubeseal --cert pub-sealed-secrets.pem --format yaml < "+ folder + "/validator-keys-node-" + str(x) + ".yaml > "+ network + "/sealed-secrets/validator-keys-node-" + str(x) + "-sealed.yaml -n " + namespace)

def merge_JsonFiles(filename):
        result = list()
        for f1 in filename:
            with open(f1, 'r') as infile:
                result.extend(json.load(infile))

        with open('deposit_data.json', 'w') as output_file:
            json.dump(result, output_file)

def concat():
    depositDataFiles = []
    for filename in glob.iglob('l15-dev/**/*deposit_data*.json', recursive=True):
        depositDataFiles.append(filename)

    depositDataFiles.sort()
    merge_JsonFiles(depositDataFiles)

def createWallets(network, index):

    os.system('/usr/local/bin/lukso-validator accounts import --keys-dir ./l15-dev/node-'+index+'/validator_keys --wallet-dir ./l15-dev/node-'+index+'/wallet --account-password-file ./keyspw.txt --wallet-password-file ./walletpw.txt'),

if __name__ == "__main__":
    main()
    # concat()
