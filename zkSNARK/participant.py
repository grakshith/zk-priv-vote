import sys
from web3 import Web3
from primes import generate_prime_pair
from transaction_utils import *
from crypto import *
from proof_function import *


# protocol flags
anonymous = True

# dict of public keys of all participants
public_keys = {1: "", 2:"", 3:""}  

# participant details
participant_id = 1 
public_key = ""
private_Key = ""
contestant = False
voters = len(public_keys)  

print("My id:", participant_id)

# script to turn-on mining --  we will do the enode connection beforehand and just turn on mining at this point if possible


print("Mining started")

# initial web3 setup
web3 = Web3(Web3.IPCProvider('/home/chinmay/.ethereum/net2020/geth.ipc'))
account_1 = web3.eth.accounts[0]
web3.geth.personal.unlock_account(web3.eth.accounts[0], "pass1")


# phase 1: blocks 1-300 -- declare candidacy and publish product
if contestant:
    message = "01 Contestant id: {}".format(participant_id)  
    sendTransaction(web3, account_1, message, private_Key)

if anonymous:
    prime_pair = generate_prime_pair(16)
    n_i = prime_pair[0] * prime_pair[1]
    message = "02 Voter id: {} {}".format(participant_id, n_i)
    sendTransaction(web3, account_1, message, private_Key)

# intermediate-phase 1 -- blocks 301-700 -- gather products to form N and gather list of contestants
contestants, participants_ni = gather_contestants_participants_ni(web3, public_keys, anonymous)
print("contestants: ", contestants)

if anonymous:
    N = 1
    for participant in participants_ni:
        N *= participants_ni[participant]

# phase 2 -- blocks 701 - 1000 -- voting 
vote = int(input("Enter contestant_id to vote for: ")) # here, we dont need a timeout because if a voter takes more time it is her loss


if anonymous:
    # send encrypted votes
    message = "03 {} {}".format(prime_pair[0], prime_pair[1])
    contestant_pk = public_keys[vote] # contestant is the person to vote
    encrypted_message = rsa_encrypt(message, contestant_pk)
    sendTransaction(web3, account_1, encrypted_message, private_Key) # potential issue -- need to convert bytes to hex

else:
    message = "03 vote: {}".format(vote)
    sendTransaction(web3, account_1, message, private_Key)


# intermediate phase 2 -- blocks 1001 - 1400 -- honest agents and contestants discard non-encrypted factors to compute new N, contestant count votes
# blocks 1401 - 1800 -- contestants find proofs and share the proof

if contestant:
    # update N, voters; gather legit votes; construct proof
    discard_factors, legit_factors = find_votes(web3, private_Key)
    N, voters = updated_voters(N, voters, discard_factors)

    # call proof function with N, legit factors and voters



else:
    # update N, voters
    discard_factors = non_encrypted_factors(web3,private_Key)
    N, voters = updated_voters(N, voters, discard_factors)




# phase 3 -- blocks 1801 - 2100 -- honest agents verify proofs (by checking blocks 1400- 1800) and determine the winner

