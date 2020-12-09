import sys
import time
import subprocess
from web3 import Web3
from primes import generate_prime_pair
from transaction_utils import *
from crypto import *
# from proof_function import *

#constant parameters
start_block = 1445
phase_0_end = start_block + 20
inter_phase_0_end = start_block + 40
phase_1_end = start_block + 60
inter_phase_1_end = start_block + 80
phase_2_end = start_block + 100
inter_phase_2_mid = start_block + 120
inter_phase_2_end = start_block + 140    #1400 is an in-between milestone?
phase_3_end = start_block + 160

# protocol flags
anonymous = True
debug = True
contestant = True

# dict of public keys of all participants and winning threshold
public_keys = {}  
threshold = 2

# participant details
if anonymous: 
    public_key, private_key = gen_keys()
participant_id = 1

# initial web3 setup
# web3 = Web3(Web3.IPCProvider('/home/chinmay/.ethereum/net2020/geth.ipc'))
# web3 = Web3(Web3.IPCProvider('/home/rakshith/.ethereum/net2020/geth.ipc')) 
web3 = Web3(Web3.IPCProvider('/home/radha/Documents/ucsb/fall20/291d/project/private-ethereum/net2020/geth.ipc'))

account_1 = web3.eth.accounts[0]
web3.geth.personal.unlock_account(web3.eth.accounts[0], "pass1")

# with open('/home/chinmay/.ethereum/net2020/keystore/UTC--2020-12-05T08-59-15.727899516Z--00b74e369f5c7c6edd99ba302b1b309cbe8a46ac') as keyfile:
# with open('/home/rakshith/.ethereum/net2020/keystore/UTC--2020-12-07T22-27-05.479330396Z--4445f43ab37a872ab5204cf878fc3d32d18ae26c') as keyfile: 
with open('/home/radha/Documents/ucsb/fall20/291d/project/private-ethereum/net2020/keystore/UTC--2020-11-29T02-40-28.577278542Z--34b45153f30f346ebe99c8db91c38d67ecf535da') as keyfile:
    encrypted_key = keyfile.read()
    bc_key = web3.eth.account.decrypt(encrypted_key, 'pass1')


# script to turn-on mining --  participant.py should be run after connecting peers manually using enode
web3.geth.miner.start(1)

print("Mining started")

while web3.eth.blockNumber < start_block:
    continue

#phase 0: blocks 1-100 -- publish public key
if anonymous:
    message = str.encode("00|") + public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    sendTransaction(web3, account_1, message, bc_key, private_key)
else:
    message = str.encode("00|")
    sendTransaction(web3, account_1, message, bc_key)

if debug:
    print('sent transaction')

#wait for next phase
while web3.eth.blockNumber < phase_0_end:
    continue

if debug:
    print("Phase 0 done.")

#intermediate-phase 0: gather all public keys
if anonymous:
    public_keys = get_public_keys(web3, start_block, phase_0_end)
    # voters = len(public_keys)
else:
    voter_list = list_voters(web3, start_block, phase_0_end)
    voters = len(voter_list)

if debug:
    print('got public keys')
    print(public_keys)
#wait for next phase
while web3.eth.blockNumber < inter_phase_0_end:
    continue

if debug:
    print("Inter Phase 0 done.")

# phase 1: blocks 100-300 -- declare candidacy and publish product
if contestant:
    message = str.encode("01")   
    print("contestant message: ", message)
    if anonymous:
        txhash = sendTransaction(web3, account_1, message, bc_key, private_key)
    else:
        txhash = sendTransaction(web3, account_1, message, bc_key)

time.sleep(15)

if contestant:
    my_id = web3.eth.getTransaction(txhash)['from']

if anonymous:
    prime_pair = generate_prime_pair(16)
    n_i = prime_pair[0] * prime_pair[1]
    message = str.encode("02|{}".format(n_i))
    sendTransaction(web3, account_1, message, bc_key, private_key)

if debug:
    print('published product')
#wait for next phase
while web3.eth.blockNumber < phase_1_end:
    continue

if debug:
    print("Phase 1 done.")

# intermediate-phase 1 -- blocks 301-700 -- gather products to form N and gather list of contestants

#Stores only most recent puzzle put on bc because of dictionary
contestants, participants_ni = gather_contestants_participants_ni(web3, public_keys, phase_0_end+1, phase_1_end, anonymous)
if anonymous:
    voters = len(participants_ni)

print("contestants: ")
for i, c in enumerate(contestants):
    print("{}: {}".format(i, c))

if anonymous:
    N = 1
    for participant in participants_ni:
        N *= participants_ni[participant]

#wait for next phase
while web3.eth.blockNumber < inter_phase_1_end:
    continue

if debug:
    if anonymous:
        print('puzzles: ', participants_ni)
    print("Inter Phase 1 done.")

# phase 2 -- blocks 701 - 1000 -- voting 
vote = int(input("Enter contestant_id to vote for: ")) # here, we dont need a timeout because if a voter takes more time it is her loss


if anonymous:
    # send encrypted votes
    message = "03|{}|{}".format(prime_pair[0], prime_pair[1])
    contestant_pk = public_keys[contestants[vote]] 
    encrypted_message = rsa_encrypt(message, contestant_pk)
    sendTransaction(web3, account_1, encrypted_message, bc_key, private_key) # potential issue -- need to convert bytes to hex

else:
    message = str.encode("03|vote:|{}".format(vote))
    sendTransaction(web3, account_1, message, bc_key)

#wait for next phase
while web3.eth.blockNumber < phase_2_end:
    continue

if debug:
    print("Phase 2 done.")

# intermediate phase 2 -- blocks 1001 - 1400 -- honest agents and contestants discard non-encrypted factors to compute new N, contestant count votes
# blocks 1401 - 1800 -- contestants find proofs and share the proof

if contestant and anonymous:
    # update N, voters; gather legit votes; construct proof
    discard_factors, legit_factors, del_list = find_votes(web3, private_key, inter_phase_1_end + 1, phase_2_end)
    N, voters = updated_voters(N, voters, discard_factors, participants_ni, del_list)

    list_factors = []
    for i in legit_factors:
        for x in i:
            list_factors.append(x)
    # call proof function with N, legit factors and voters
    subprocess.call(["python3", "proof_function.py", "{}|{}".format(N, voters), "|".join(list_factors)])
    with open ('pysnark_log', "r") as f:
        proof = f.read()
    with open ('pysnark_vk', "r") as f:
        vk = f.read()
    with open ('pysnark_pubvals', "r") as f:
        pubvals = f.read()
    message = str.encode("04|" + proof + "|" + vk + "|" + pubvals)
    sendTransaction(web3, account_1, message, bc_key, private_key)


elif anonymous:
    # Voter in anonymous protocol: update N, voters
    discard_factors, del_list = non_encrypted_factors(web3,private_key, inter_phase_1_end + 1, phase_2_end )
    N, voters = updated_voters(N, voters, discard_factors, participants_ni, del_list)

else:
    # candidate or voter in non-anonymous
    vote_count = get_vote_count(web3, contestants, inter_phase_1_end + 1, phase_2_end)
    if contestant and vote_count[my_id] > threshold:
        message = str.encode("04|Winner")
        sendTransaction(web3, account_1, message, bc_key)

if debug:
    print("Inter Phase 2 done.")
    if anonymous:
        print("New N: ", N)
    print("New voters: ", voters)

#wait for next phase
while web3.eth.blockNumber < inter_phase_2_end:
    continue

# phase 3 -- blocks 1801 - 2100 -- honest agents verify proofs (by checking blocks 1400- 1800) and determine the winner

if anonymous:
    # honest agents should verify proofs and put true or false on the blockchain
    # pass
    proofs = get_proofs(web3, contestants, inter_phase_2_end+1, phase_3_end)
    for proof in proofs:
        with open('pysnark_log', "w") as f:
            f.write(proof[0])
        with open('pysnark_vk', "w") as f:
            f.write(proof[1])
        with open('pysnark_pubvals', "w") as f:
            f.write(proof[2])
        subprocess.call(["python3", "verify.py"])

else:
    # honest agents publish true or false
    winners = get_winners(web3, contestants, inter_phase_2_end+1, phase_3_end)
    non_winners = set()
    for claimed_winner in winners:
        if vote_count[claimed_winner] < threshold:
            non_winners.add(claimed_winner)
    for non_winner in non_winners:
        message = str.encode("False|{}".format(non_winner))
        sendTransaction(web3, account_1, message, bc_key)


