from web3 import Web3

def string_to_hex(s = ""):
    hex_s = ''.join(hex(ord(x))[2:] for x in s)
    return hex_s

def hex_to_string(s):
    string = bytes.fromhex(s[2:]).decode('utf-8')
    return string


web3 = Web3(Web3.IPCProvider('/home/chinmay/.ethereum/net2020/geth.ipc'))
#web3 = Web3(Web3.IPCProvider('./path/to/geth.ipc')

print(web3.isConnected())   # true if connection is successful

account_1 = web3.eth.accounts[0]    # local eth account[0]
account_2 = "0x34b45153f30f346ebe99c8db91c38d67ecf535da"    # required only for balance transfer applications

# extracting private key to unlock the local account
with open('/home/chinmay/.ethereum/net2020/keystore/UTC--2020-11-29T02-40-28.577278542Z--34b45153f30f346ebe99c8db91c38d67ecf535da') as keyfile:
    encrypted_key = keyfile.read()
    private_key = web3.eth.account.decrypt(encrypted_key, 'pass1')


print(web3.geth.personal.unlock_account(web3.eth.accounts[0], "pass1"))


# sending a transaction

nonce_1 = web3.eth.getTransactionCount(account_1)

data = "00 Hey there!"

tx = {
    'nonce': nonce_1,
    'value': web3.toWei(0, 'ether'), 
    'gas': 0,
    'gasPrice': web3.toWei('0', 'gwei'),
    'data' : string_to_hex(data),
}

signed_tx = web3.eth.account.signTransaction(tx, private_key)

print('signed tx:', signed_tx) # just for debugging

tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)


# retrieving latest block which with non-empty transactions 
# (to be run at other client's end which did not send the transaction)
# (to run at the client which send the transaction, change latest -= 1 to latest += 1 in the while loop due to delay in putting transaction in a mined block)

latest = web3.eth.blockNumber

print('latest block: ', web3.eth.getBlock(latest))


while latest > 0:
    if len(web3.eth.getBlock(latest).transactions) != 0:
        block_hash = web3.eth.getBlock(latest).transactions[0]
        break
    else:
        latest -= 1

transaction = web3.eth.getTransaction(block_hash)

print("transaction input: ", transaction.input)
print('transaction-input: ', bytes.fromhex(transaction.input[2:]))
