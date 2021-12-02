# cli.py
from mnemonic import Mnemonic
import click
import os
import glob
import json
import re
import wget
from types import SimpleNamespace

CMD_COLOR = "\033[96m"
OK_COLOR = "\033[92m"

DEPOSIT_CLI_URL = "https://github.com/lukso-network/network-deposit-cli/releases/download/v1.2.6-LUKSO/lukso-deposit-cli-Linux-x86_64"


@click.command()
def main():

    config_dict = {
        "network": "l15-dev",
        "nodes": 8,
        "validatorsPerNode": 10,
        "namespace": "l15-dev",
        "depositCliName": DEPOSIT_CLI_URL.split("/")[-1],
        "folder": "",
    }

    config = SimpleNamespace(**config_dict)

    print("Create nescessary folder structure for " + config.network)
    try:
        os.mkdir(config.network)
        os.mkdir(config.network + "/sealed-secrets")
    except FileExistsError:
        print(
            f'\033[91mThe folder "{os.getcwd()}/{config.network}" already exists. \nPlease make a backup and delete the folder, then try again.'
        )
        return

    print(CMD_COLOR + "Download lukso-deposit-cli")
    wget.download(DEPOSIT_CLI_URL)
    os.system(f"mv {config.depositCliName} lukso-deposit-cli >/dev/null")
    os.system(f"chmod +x lukso-deposit-cli >/dev/null")
    print(OK_COLOR + "\nSuccessful\n")
    print(CMD_COLOR + "Update Sealed Secrets Public Key...")

    seal_secrets_cmd = """\
        kubeseal 
            --fetch-cert 
            --controller-name=sealed-secrets 
            --controller-namespace=sealed-secrets 
            > pub-sealed-secrets.pem 
            -n sealed-secrets\
    """
    excecute_command(seal_secrets_cmd)

    print(CMD_COLOR + "Starting key generation")
    for nodeNumber in range(config.nodes):
        print("\033[1mNode " + str(nodeNumber) + ":")
        folder, words = create_mnemonic(config.network, str(nodeNumber))
        create_keys(folder, config.network, words, config.validatorsPerNode)
        create_wallets(config.network, str(nodeNumber))
        create_plain_k8s_secrets(folder, config.namespace, str(nodeNumber))
        seal_secrets(folder, config.network, config.namespace, str(nodeNumber))

    # Create a concatenated deposit_data.json file.
    concat()


def merge_JsonFiles(files):
    files.sort()
    result = list()
    for file in files:
        with open(file, "r") as data:
            result.extend(json.load(data))

    with open("deposit_data.json", "w") as output_file:
        json.dump(result, output_file)


def concat():
    depositDataFiles = []
    for filename in glob.iglob("l15-dev/**/*deposit_data*.json", recursive=True):
        depositDataFiles.append(filename)

    merge_JsonFiles(depositDataFiles)


def create_wallets(network, index):
    print(CMD_COLOR + "Generating Wallet...")
    cmd = """\
        /usr/local/bin/lukso-validator 
            accounts import
            --keys-dir              ./{network}/wallet-{index}/validator_keys 
            --wallet-dir            ./{network}/wallet-{index}/wallet 
            --account-password-file ./keys-pw.txt 
            --wallet-password-file  ./password.txt
        >/dev/null\
    """.format(
        index=index, network=network
    )

    excecute_command(cmd)


def create_mnemonic(network, nodeNumber):
    print(CMD_COLOR + "  Generating Mnemonic...")
    mnemo = Mnemonic("english")
    words = mnemo.generate(strength=256)

    folder = network + "/wallet-" + str(nodeNumber)
    os.mkdir(folder)
    f = open(folder + "/mnemonic", "x")
    f.write(words)
    print(OK_COLOR + "    Successful\n")

    return folder, words


def create_keys(folder, network, words, validatorsPerNode):
    print(CMD_COLOR + "  Generating Keys...")
    cmd = """\
        ./lukso-deposit-cli 
            existing-mnemonic 
            --folder {folder}
            --num_validators {validatorsPerNode}
            --validator_start_index 0 
            --keystore_password 12345678 
            --chain {network}
            --mnemonic "{words}"
        >/dev/null\
    """.format(
        folder=folder, network=network, words=words, validatorsPerNode=validatorsPerNode
    )

    excecute_command(cmd)


def create_plain_k8s_secrets(folder, namespace, nodeNumber):
    print(CMD_COLOR + "  Generating plain K8S secrets...")
    cmd = """\
        kubectl create secret generic validator-keys-node-{nodeNumber}
            --from-file={folder}/wallet/direct/accounts/all-accounts.keystore.json
            --dry-run=client -o yaml -n {namespace}
            > {folder}/validator-keys-node-{nodeNumber}.yaml 
        \
        """.format(
        folder=folder, nodeNumber=nodeNumber, namespace=namespace
    )

    excecute_command(cmd)


def seal_secrets(folder, network, namespace, nodeNumber):
    print(CMD_COLOR + "  Sealing the Secrets...")
    cmd = """\
        kubeseal 
        --cert pub-sealed-secrets.pem 
        --format yaml 
        < {folder}/validator-keys-node-{nodeNumber}.yaml 
        > {network}/sealed-secrets/validator-keys-node-{nodeNumber}-sealed.yaml
        -n {namespace}\
        """.format(
        folder=folder, network=network, namespace=namespace, nodeNumber=nodeNumber
    )

    excecute_command(cmd)


def excecute_command(cmd):
    cmd = cmd.lstrip().rstrip()
    cmd = re.sub(r"( )( *)", r"\g<1>", cmd)
    cmd = re.sub(r"\n", "", cmd)
    os.system(cmd)
    print(OK_COLOR + "    Successful\n")


if __name__ == "__main__":
    main()
