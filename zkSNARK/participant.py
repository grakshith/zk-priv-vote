import sys
import time
import json
import subprocess
import statistics
from web3 import Web3
from primes import generate_prime_pair
from transaction_utils import *
from crypto import *
# from proof_function import *

runtimes = {}
msg_size = 0
r_msg_size = 0
#constant parameters
start_block = 1975
offset = 10
phase_0_end = start_block + 2*offset
inter_phase_0_end = start_block + 4*offset
phase_1_end = start_block + 6*offset
inter_phase_1_end = start_block + 8*offset
phase_2_end = start_block + 10*offset
# inter_phase_2_mid = start_block + 12*offset
inter_phase_2_end = start_block + 12*offset    #1400 is an in-between milestone?
phase_3_end = start_block + 14*offset

# protocol flags
anonymous = True
debug = True
contestant = False

# dict of public keys of all participants and winning threshold
public_keys = {}
threshold = 1

prog_start_time = time.process_time()
start_time = time.process_time()
# participant details
if anonymous:
    public_key, private_key = gen_keys()

# initial web3 setup
# web3 = Web3(Web3.IPCProvider('/home/chinmay/.ethereum/net2020/geth.ipc'))
# web3 = Web3(Web3.IPCProvider('/home/rakshith/.ethereum/net2020/geth.ipc'))
web3 = Web3(Web3.IPCProvider('/home/radha/Documents/ucsb/fall20/291d/project/private-ethereum/net2020/geth.ipc'))

account_1 = web3.eth.accounts[0]
web3.geth.personal.unlock_account(web3.eth.accounts[0], "pass1")
# web3.geth.personal.unlock_account(web3.eth.accounts[0], "1234")

# with open('/home/chinmay/.ethereum/net2020/keystore/UTC--2020-12-05T08-59-15.727899516Z--00b74e369f5c7c6edd99ba302b1b309cbe8a46ac') as keyfile:
# with open('/home/rakshith/.ethereum/net2020/keystore/UTC--2020-12-07T22-27-05.479330396Z--4445f43ab37a872ab5204cf878fc3d32d18ae26c') as keyfile:
with open('/home/radha/Documents/ucsb/fall20/291d/project/private-ethereum/net2020/keystore/UTC--2020-11-29T02-40-28.577278542Z--34b45153f30f346ebe99c8db91c38d67ecf535da') as keyfile:
    encrypted_key = keyfile.read()
    bc_key = web3.eth.account.decrypt(encrypted_key, 'pass1')
    # bc_key = web3.eth.account.decrypt(encrypted_key, '1234')


# script to turn-on mining --  participant.py should be run after connecting peers manually using enode
web3.geth.miner.start(1)

print("Mining started")

runtimes['setup'] = time.process_time() - start_time

while web3.eth.blockNumber < start_block:
    continue

start_time = time.process_time()
#phase 0: blocks 1-100 -- publish public key
if anonymous:
    message = str.encode("00|") + public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    txhash, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size)
else:
    message = str.encode("00|")
    txhash, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size)

if debug:
    print('sent transaction')

runtimes['0a'] = time.process_time() - start_time
#wait for next phase
while web3.eth.blockNumber < phase_0_end:
    continue

if debug:
    print("Phase 0 done.")

start_time = time.process_time()
#intermediate-phase 0: gather all public keys
if anonymous:
    public_keys, r_msg_size = get_public_keys(web3, start_block, phase_0_end, r_msg_size)
    # voters = len(public_keys)
else:
    voter_list, r_msg_size = list_voters(web3, start_block, phase_0_end, r_msg_size)
    voters = len(voter_list)

if debug:
    print('got public keys')
    print(public_keys)
runtimes['0b'] = time.process_time() - start_time
#wait for next phase
while web3.eth.blockNumber < inter_phase_0_end:
    continue

if debug:
    print("Inter Phase 0 done.")

start_time = time.process_time()
# phase 1: blocks 100-300 -- declare candidacy and publish product
if contestant:
    message = str.encode("01")
    print("contestant message: ", message)
    if anonymous:
        _, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size, private_key)
    else:
        _, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size)

time.sleep(10)

if contestant:
    my_id = web3.eth.getTransaction(txhash)['from']

if anonymous:
    prime_pair = generate_prime_pair(16)
    print("prime pair: ", prime_pair)
    n_i = prime_pair[0] * prime_pair[1]
    message = str.encode("02|{}".format(n_i))
    _, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size, private_key)

if debug:
    print('published product')

runtimes['1a'] = time.process_time() - start_time
#wait for next phase
while web3.eth.blockNumber < phase_1_end:
    continue

if debug:
    print("Phase 1 done.")

# intermediate-phase 1 -- blocks 301-700 -- gather products to form N and gather list of contestants
start_time = time.process_time()
#Stores only most recent puzzle put on bc because of dictionary
contestants, participants_ni, r_msg_size = gather_contestants_participants_ni(web3, public_keys, phase_0_end+1, phase_1_end, anonymous, r_msg_size)
if anonymous:
    voters = len(participants_ni)

print("contestants: ")
for i, c in enumerate(contestants):
    print("{}: {}".format(i, c))

if anonymous:
    N = 1
    for participant in participants_ni:
        N *= participants_ni[participant]

runtimes['1b'] = time.process_time() - start_time
#wait for next phase
while web3.eth.blockNumber < inter_phase_1_end:
    continue

if debug:
    if anonymous:
        print('puzzles: ', participants_ni)
    print("Inter Phase 1 done.")

start_time = time.process_time()
# phase 2 -- blocks 701 - 1000 -- voting
vote = int(input("Enter contestant_id to vote for: ")) # here, we dont need a timeout because if a voter takes more time it is her loss

#IF NO CONTESTANTS SKIP THIS PHASE

if anonymous:
    # send encrypted votes
    message = "03|{}|{}".format(prime_pair[0], prime_pair[1])
    contestant_pk = public_keys[contestants[vote]]
    encrypted_message = rsa_encrypt(message, contestant_pk)
    _, msg_size = sendTransaction(web3, account_1, encrypted_message, bc_key, msg_size, private_key) # potential issue -- need to convert bytes to hex

else:
    message = str.encode("03|vote:|{}".format(vote))
    _, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size)

runtimes['2'] = time.process_time() - start_time
#wait for next phase
while web3.eth.blockNumber < phase_2_end:
    continue

if debug:
    print("Phase 2 done.")

# intermediate phase 2 -- blocks 1001 - 1400 -- honest agents and contestants discard non-encrypted factors to compute new N, contestant count votes
# blocks 1401 - 1800 -- contestants find proofs and share the proof
start_time = time.process_time()
if contestant and anonymous:
    # update N, voters; gather legit votes; construct proof
    discard_factors, legit_factors, del_list, r_msg_size = find_votes(web3, public_keys, private_key, inter_phase_1_end + 1, phase_2_end, r_msg_size)
    N, voters = updated_voters(N, voters, discard_factors, participants_ni, del_list)
    print(N, voters)
    list_factors = []
    print(legit_factors)
    for i in legit_factors.values():
        for x in i:
            list_factors.append(str(x))
    # call proof function with N, legit factors and voters
    print('legit factors: ', len(legit_factors))
    if len(legit_factors) > threshold:
        subprocess.call(["python3", "proof_function.py", "{}|{}".format(N, voters), "|".join(list_factors)])
        with open ('pysnark_log', "r") as f:
            proof = f.read()
        with open ('pysnark_vk', "r") as f:
            vk = f.read()
        with open ('pysnark_pubvals', "r") as f:
            pubvals = f.read()
        message = str.encode("04|" + proof + "|" + vk + "|" + pubvals)
        _, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size, private_key)
        print('sent proof')

elif anonymous:
    # Voter in anonymous protocol: update N, voters
    discard_factors, del_list, r_msg_size = non_encrypted_factors(web3,public_keys, private_key, inter_phase_1_end + 1, phase_2_end, r_msg_size)
    N, voters = updated_voters(N, voters, discard_factors, participants_ni, del_list)

else:
    # candidate or voter in non-anonymous
    vote_count, r_msg_size = get_vote_count(web3, public_keys, contestants, inter_phase_1_end + 1, phase_2_end, r_msg_size)
    if contestant and vote_count[my_id] > threshold:
        message = str.encode("04|Winner")
        _, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size)

if debug:
    print("Inter Phase 2 done.")
    if anonymous:
        print("New N: ", N)
    print("New voters: ", voters)

runtimes['3'] = time.process_time() - start_time
#wait for next phase
while web3.eth.blockNumber < inter_phase_2_end:
    continue

# phase 3 -- blocks 1801 - 2100 -- honest agents verify proofs (by checking blocks 1400- 1800) and determine the winner
start_time = time.process_time()
if anonymous:
    # honest agents should verify proofs and put true or false on the blockchain
    # pass
    proofs, r_msg_size = get_proofs(web3, public_keys, contestants, phase_2_end+1, inter_phase_2_end, r_msg_size)
    for proof in proofs:
        with open('pysnark_log', "w") as f:
            f.write(proof[0])
        with open('pysnark_vk', "w") as f:
            f.write(proof[1])
        with open('pysnark_pubvals', "w") as f:
            f.write(proof[2])
            # f.write(str(N) + '\n' + )
        subprocess.call(["python3", "verify.py"])
    print('verification complete')

else:
    # honest agents publish true or false
    winners, r_msg_size = get_winners(web3, contestants, phase_2_end+1, inter_phase_2_end, r_msg_size)
    non_winners = set()
    for claimed_winner in winners:
        if vote_count[claimed_winner] < threshold:
            non_winners.add(claimed_winner)
    for non_winner in non_winners:
        message = str.encode("False|{}".format(non_winner))
        _, msg_size = sendTransaction(web3, account_1, message, bc_key, msg_size)

runtimes['4'] = time.process_time() - start_time
runtimes['total'] = time.process_time() - prog_start_time


print(json.dumps(runtimes))
print(msg_size)
print(r_msg_size)