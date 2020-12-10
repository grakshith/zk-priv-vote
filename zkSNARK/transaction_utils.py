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
    string = bytes.fromhex(s[2:])
    return string



# send transaction on the blockchain

def sendTransaction(web3, account, message, bc_key, private_key = None):
    nonce_1 = web3.eth.getTransactionCount(account)
    if private_key:
        signature = rsa_sign(message, private_key)
    # message = message + "--"  + signature # change signature format
    if private_key:
        message = message + str.encode("--") + signature
    else:
        message = message
    tx = {
        'nonce': nonce_1,
        'value': web3.toWei(0, 'ether'),
        'gas': 1000001,
        'gasPrice': web3.toWei('0', 'gwei'),
        'data' : string_to_hex(message),
    }
    signed_tx = web3.eth.account.signTransaction(tx, bc_key)
    #print('signed tx:', signed_tx) # just for debugging
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return tx_hash

#get all public keys of participants
def get_public_keys(web3, start, end):
    public_keys = {}
    block_number = start
    while block_number < end:
        num_transactions = len(web3.eth.getBlock(block_number).transactions)
        if num_transactions != 0:
            # print(block_number)
            for i in range(num_transactions):
                block_hash = web3.eth.getBlock(block_number).transactions[i]
                transaction = web3.eth.getTransaction(block_hash)
                # need to find sender of the transaction here (better way of doing this is welcome)
                # print(transaction.input)
                message = hex_to_string(transaction.input)
                print("Get public keys message: ", message)
                sender_id = transaction['from']
                #FIGURE OUT BYTESTRING BIT
                if message.decode().split('|')[0] == "00":
                    message = message.split(str.encode("|"))
                    # print(message)
                    key = serialization.load_pem_public_key(
                        message[-1],
                        backend=default_backend()
                    )
                    public_keys[sender_id] = key
        block_number += 1

    return public_keys

def list_voters(web3, start, end):
    voter_list = []
    block_number = start
    while block_number < end:
        num_transactions = len(web3.eth.getBlock(block_number).transactions)
        if num_transactions != 0:
            # print(block_number)
            for i in range(num_transactions):
                block_hash = web3.eth.getBlock(block_number).transactions[i]
                transaction = web3.eth.getTransaction(block_hash)
                # need to find sender of the transaction here (better way of doing this is welcome)
                # print(transaction.input)
                message = hex_to_string(transaction.input)
                sender_id = transaction['from']
                #FIGURE OUT BYTESTRING BIT
                if message.decode() == "00":
                    voter_list.append(sender_id)

        block_number += 1

    return voter_list


# find sender of the message by checking signature
def find_sender(message, transaction, public_keys):
    message, signature = message.strip().split(str.encode("--"))
    sender_id = transaction['from']
    public_key = public_keys[sender_id]
    if rsa_verify(message, signature, public_key):
        return message
    return None


def gather_contestants_participants_ni(web3, public_keys, start, end, anonymous):
    # note -> contestants list is an identical ORDERED list for all participants --> useful fact for non-secure voting
    contestants = []
    if anonymous: participants_ni = {}
    else:
        participants_ni = None
    block_number = start
    while block_number < end:
        num_transactions = len(web3.eth.getBlock(block_number).transactions)
        if num_transactions != 0:
            for i in range(num_transactions):
                block_hash = web3.eth.getBlock(block_number).transactions[i]
                transaction = web3.eth.getTransaction(block_hash)
                # need to find sender of the transaction here (better way of doing this is welcome)
                message = hex_to_string(transaction.input)
                message = find_sender(message, transaction, public_keys)
                if(not message):
                    continue
                #ADD IN VERIFICATION
                sender_id = transaction['from']

                # if not sender_id:
                #     # case when malicious participant sends an incorrect signature
                #     continue
                message = message.strip().split(str.encode("|"))
                print('msg: ', message)
                if message[0].decode() == "01":
                    if message[-1].decode().isdigit():
                        contestants.append(sender_id)
                if anonymous and message[0].decode() == "02":
                    # valid n_i message
                    if message[-1].decode().isdigit():
                        participants_ni[sender_id] = int(message[-1].decode())
        block_number += 1
    return list(set(contestants)), participants_ni

def non_encrypted_factors(web3, private_key, start, end):
    # assumption --  these messages come in specified format
    non_encrypted_factors = set()
    block_number = start
    legit_votes = set()
    del_list = []
    while block_number < end:
        num_transactions = len(web3.eth.getBlock(block_number).transactions)
        if num_transactions != 0:
            for i in range(num_transactions):
                block_hash = web3.eth.getBlock(block_number).transactions[i]
                transaction = web3.eth.getTransaction(block_hash)
                message = hex_to_string(transaction.input)
                message = find_sender(message, transaction, public_keys)
                if(not message):
                    continue
                if transaction['from'] in legit_votes:
                    #Repeated vote, record the participant
                    del_list.append(transaction['from'])
                elif rsa_decrypt(message, private_key).split(str.encode("|"))[0] == "03":
                    pass
                elif message.split('|')[0].decode() == "03":
                    message = message.strip().split('|')
                    non_encrypted_factors.add(int(message[-1]))
                    non_encrypted_factors.add(int(message[-2]))
                legit_votes.add(transaction['from'])
        block_number+= 1

    return non_encrypted_factors, list(set(del_list))


def updated_voters(N, voters, discard_factors, participants_ni, del_list):
    counter = 0
    for factor in discard_factors:
        new_N = N / factor
        if type(new_N) == int:
            # legitimate factor; other case is when malicious agents put random numbers on the blockchain
            N = new_N
            counter += 1

    #Remove puzzles by people who voted multiple times
    for participant in del_list:
        N = N/participants_ni[participant]
        counter += 1

    voters = voters - counter // 2 # decrease number of legit voters to pass to the verification function
    return N, voters

def find_votes(web3, private_key, start, end):
    non_encrypted_factors = set()
    # legit_factors = set()
    legit_factors = {}
    del_list = []
    block_number = start
    while block_number < end:
        num_transactions = len(web3.eth.getBlock(block_number).transactions)
        if num_transactions != 0:
            for i in range(num_transactions):
                block_hash = web3.eth.getBlock(block_number).transactions[i]
                transaction = web3.eth.getTransaction(block_hash)
                message = hex_to_string(transaction.input)
                message = find_sender(message, transaction, public_keys)
                if(not message):
                    continue
                if transaction['from'] in legit_factors:
                    #Repeated vote, record the participant
                    del_list.append(transaction['from'])
                # elif message.split(str.encode("|"))[0].decode() == "03":
                #     message = message.strip().split(str.encode("|"))
                #     non_encrypted_factors.add(int(message[-1].decode()))
                #     non_encrypted_factors.add(int(message[-2].decode()))
                else:
                    try:
                        if rsa_decrypt(message, private_key).split("|")[0] == "03":
                            message = rsa_decrypt(message, private_key).strip().split("|")
                        # legit_factors.add(int(message[-1]))
                        # legit_factors.add(int(message[-2]))
                        # FACTORS ARE NOW LIST OF TUPLES
                        legit_factors[transaction['from']] = (int(message[-1]), int(message[-2]))
                    except:
                        pass

        block_number+= 1

    #Delete the newest vote of participants who voted multiple times
    for key in list(set(del_list)):
        del legit_factors[key]

    return non_encrypted_factors, legit_factors, del_list

# for non-anonymous case, this function finds votes by non-malicious agents
def get_vote_count(web3, contestants, start, end):
    legit_votes = dict()
    del_list = []
    block_number = start
    while block_number < end:
        if len(web3.eth.getBlock(block_number).transactions) != 0:
            block_hash = web3.eth.getBlock(block_number).transactions[0]
            transaction = web3.eth.getTransaction(block_hash)
            message = hex_to_string(transaction.input)
            if transaction['from'] in legit_votes:
                #Repeated vote, record the participant
                del_list.append(transaction['from'])
            elif message.split(str.encode("|"))[0].decode() == "03":
                # record a vote
                message = message.strip().split(str.encode("|"))
                legit_votes[transaction['from']] = int(message[-1])
        block_number += 1
    #Delete the newest vote of participants who voted multiple times
    for key in list(set(del_list)):
        del legit_votes[key]

    # vote counting
    vote_count = dict()
    for candidate in legit_votes:
        if legit_votes[candidate] in vote_count:
            vote_count[legit_votes[candidate]] += 1
        else:
             vote_count[legit_votes[candidate]] = 1
    return vote_count

def get_winners(web3, contestants, start, end):
    winners_id = set()
    block_number = start
    while block_number < end:
        num_transactions = len(web3.eth.getBlock(block_number).transactions)
        if num_transactions != 0:
            for i in range(num_transactions):
                block_hash = web3.eth.getBlock(block_number).transactions[i]
                transaction = web3.eth.getTransaction(block_hash)
                message = hex_to_string(transaction.input)
                if message.split(str.encode("|"))[0].decode() == "04":
                    # record winner
                    winners_id.add(transaction['from'])
        block_number += 1

    # winner indices from the list of contestants
    winners = []
    for winner in winners_id:
        winners.append(contestants.index(winner))
    return winners


def get_proofs(web3, contestants, start, end):
    proofs = []
    block_number = start
    while block_number < end:
        num_transactions = len(web3.eth.getBlock(block_number).transactions)
        if num_transactions != 0:
            for i in range(num_transactions):
                block_hash = web3.eth.getBlock(block_number).transactions[i]
                transaction = web3.eth.getTransaction(block_hash)
                message = hex_to_string(transaction.input)
                message = find_sender(message, transaction, public_keys)
                if(not message):
                    continue
                if message.split(str.encode("|"))[0].decode() == "04":
                    # record winner
                    message = message.decode()
                    proofs.append(message.split("|")[1:])

        block_number +=1
    return proofs
