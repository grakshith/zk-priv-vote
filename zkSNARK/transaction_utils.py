from web3 import Web3
from crypto import *



def string_to_hex(s):
    if type(s) == str:
        print("type1")
        hex_s = ''.join(hex(ord(x))[2:] for x in s)
        return hex_s
    else:
        # type(s) = bytes
        print("type 2")
        hex_s = s.hex()
        return hex_s


def hex_to_string(s):
    string = bytes.fromhex(s)
    return string

    

# send transaction on the blockchain

def sendTransaction(web3, account, message, private_key):
    nonce_1 = web3.eth.getTransactionCount(account)
    signature = rsa_sign(message, private_key)
    message = message + "--"  + signature 
    tx = {
        'nonce': nonce_1,
        'value': web3.toWei(0, 'ether'), 
        'gas': 0,
        'gasPrice': web3.toWei('0', 'gwei'),
        'data' : string_to_hex(message),
    }
    signed_tx = web3.eth.account.signTransaction(tx)
    #print('signed tx:', signed_tx) # just for debugging
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return tx_hash


# find sender of the message by checking signature
def find_sender(message, public_keys):
    message, signature = message.strip().split("--")
    sender_id = None
    for participant in public_keys:
        if rsa_verify(message, signature, public_keys[participant]):
            sender_id = participant
    return message, sender_id


def gather_contestants_participants_ni(web3, public_keys):
    contestants = set()
    participants_ni = {}
    block_number = 1
    while block_number < 301:
        if len(web3.eth.getBlock(block_number).transactions) != 0:
            block_hash = web3.eth.getBlock(block_number).transactions[0]
            transaction = web3.eth.getTransaction(block_hash)
            # need to find sender of the transaction here (better way of doing this is welcome)
            message = hex_to_string(transaction.input)
            message, sender_id = find_sender(message, public_keys)
            if not sender_id:
                # case when malicious participant sends an incorrect signature
                continue
            message = message.strip().split()
            if message[0] == "01":
                if message[-1].isdigit():
                    contestants.add(int(message[-1]))
            if message[0] == "02":
                # valid n_i message
                if message[-1].isdigit():
                    participants_ni[sender_id] = int(message[-1])
        block_number += 1
    return contestants, participants_ni

def non_encrypted_factors(web3, private_key):
    # assumption --  these messages come in specified format
    non_encrypted_factors = set()
    block_number = 1001
    while block_number < 1401:
        if len(web3.eth.getBlock(block_number).transactions) != 0:
            block_hash = web3.eth.getBlock(block_number).transactions[0]
            transaction = web3.eth.getTransaction(block_hash)
            message = hex_to_string(transaction.input)
            if rsa_decrypt(message, private_key).split()[0] == "03":
                pass
            elif str(message, 'utf-8').split()[0] == "03":
                message = message.strip().split()
                non_encrypted_factors.add(int(message[-1])) 
                non_encrypted_factors.add(int(message[-2]))
        block_number+= 1
    return non_encrypted_factors


def updated_voters(N, voters, discard_factors):
    counter = 0
    for factor in discard_factors:
        new_N = N / factor
        if type(new_N) == int:
            # legitimate factor; other case is when malicious agents put random numbers on the blockchain
            N = new_N
            counter += 1
    voters = voters - counter // 2 # decrease number of legit voters to pass to the verification function
    return N, voters

def find_votes(web3, private_key):
    non_encrypted_factors = set()
    legit_factors = set()
    block_number = 1001
    while block_number < 1401:
        if len(web3.eth.getBlock(block_number).transactions) != 0:
            block_hash = web3.eth.getBlock(block_number).transactions[0]
            transaction = web3.eth.getTransaction(block_hash)
            message = hex_to_string(transaction.input)
            if rsa_decrypt(message, private_key).split()[0] == "03":
                # legit voters
                message = message.strip().split()
                legit_factors.add(int(message[-1])) 
                legit_factors.add(int(message[-2]))
            elif str(message, 'utf-8').split()[0] == "03":
                message = message.strip().split()
                non_encrypted_factors.add(int(message[-1])) 
                non_encrypted_factors.add(int(message[-2]))
        block_number+= 1
    return non_encrypted_factors, legit_factors