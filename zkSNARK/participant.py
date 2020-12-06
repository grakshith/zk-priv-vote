import sys
from web3 import Web3
from primes import generate_prime_pair
from transaction_utils import *
from crypto import *
from proof_function import *

#constant parameters
start_block = 1
phase_0_end = 100
inter_phase_0_end = 200
phase_1_end = 300
inter_phase_1_end = 700
phase_2_end = 1000
inter_phase_2_mid = 1400
inter_phase_2_end = 1800    #1400 is an in-between milestone?
phase_3_end = 2100

# protocol flags
anonymous = True
debug = True

# dict of public keys of all participants
public_keys = {}  

# participant details
participant_id = 1 
public_key, private_key = gen_keys()
contestant = False
  

print("My id:", participant_id)

# initial web3 setup
# web3 = Web3(Web3.IPCProvider('/home/chinmay/.ethereum/net2020/geth.ipc'))
web3 = Web3(Web3.IPCProvider('/home/radha/Documents/ucsb/fall20/291d/project/private-ethereum/net2020/geth.ipc'))

account_1 = web3.eth.accounts[0]
web3.geth.personal.unlock_account(web3.eth.accounts[0], "pass1")


# script to turn-on mining --  we will do the enode connection beforehand and just turn on mining at this point if possible
web3.geth.miner.start(1)

print("Mining started")


#phase 0: blocks 1-100 -- publish public key
if anonymous:
    message = str.encode("00 ") + public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    sendTransaction(web3, account_1, message, private_key)

#wait for next phase
while web3.eth.blockNumber < phase_0_end:
    continue

if debug:
    print("Phase 0 done.")

#intermediate-phase 0: gather all public keys
if anonymous:
    public_keys = get_public_keys(web3, start_block, phase_0_end)
    # voters = len(public_keys)

#wait for next phase
while web3.eth.blockNumber < inter_phase_0_end:
    continue

if debug:
    print("Inter Phase 0 done.")

# phase 1: blocks 100-300 -- declare candidacy and publish product
if contestant:
    message = "01 Contestant id: {}".format(participant_id)  
    sendTransaction(web3, account_1, message, private_key)

if anonymous:
    prime_pair = generate_prime_pair(16)
    n_i = prime_pair[0] * prime_pair[1]
    message = "02 Voter id: {} {}".format(participant_id, n_i)
    sendTransaction(web3, account_1, message, private_key)

#wait for next phase
while web3.eth.blockNumber < phase_1_end:
    continue

if debug:
    print("Phase 1 done.")

# intermediate-phase 1 -- blocks 301-700 -- gather products to form N and gather list of contestants

#Stores only most recent puzzle put on bc because of dictionary
contestants, participants_ni = gather_contestants_participants_ni(web3, public_keys, phase_0_end+1, phase_1_end, anonymous)
voters = len(participants_ni)

print("contestants: ", contestants)

if anonymous:
    N = 1
    for participant in participants_ni:
        N *= participants_ni[participant]

#wait for next phase
while web3.eth.blockNumber < inter_phase_1_end:
    continue

if debug:
    print(participants_ni)
    print("Inter Phase 1 done.")

# phase 2 -- blocks 701 - 1000 -- voting 
vote = int(input("Enter contestant_id to vote for: ")) # here, we dont need a timeout because if a voter takes more time it is her loss


if anonymous:
    # send encrypted votes
    message = "03 {} {}".format(prime_pair[0], prime_pair[1])
    contestant_pk = public_keys[vote] # contestant is the person to vote
    encrypted_message = rsa_encrypt(message, contestant_pk)
    sendTransaction(web3, account_1, encrypted_message, private_key) # potential issue -- need to convert bytes to hex

else:
    message = "03 vote: {}".format(vote)
    sendTransaction(web3, account_1, message, private_key)

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

    # call proof function with N, legit factors and voters


elif anonymous:
    # update N, voters
    discard_factors, del_list = non_encrypted_factors(web3,private_key, inter_phase_1_end + 1, phase_2_end )
    N, voters = updated_voters(N, voters, discard_factors, participants_ni, del_list)

if debug:
    print("Inter Phase 2 done.")
    print("New N: ", N)
    print("New voters: ", voters)

#wait for next phase
while web3.eth.blockNumber < inter_phase_3_end:
    continue

# phase 3 -- blocks 1801 - 2100 -- honest agents verify proofs (by checking blocks 1400- 1800) and determine the winner

