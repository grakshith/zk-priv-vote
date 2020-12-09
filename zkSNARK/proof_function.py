import sys
import faulthandler
from my_pysnark.runtime import PrivVal, PubVal, snark, ignore_errors
from my_pysnark.branching import BranchingValues, if_then_else, _if, _elif, _else, _endif, _range, _while, _endwhile, _endfor, _breakif
from tuple_compare import tuple_compare
from primes import generate_prime_number
import time
import statistics
import my_pysnark.libsnark.backend as backend

faulthandler.enable()
ignore_errors(True)

# @snark
# def tuple_compare(x, y):
#     _ = BranchingValues()
#     r1 = (x[0] == y[0])
#     r2 = (x[1] == y[1])
#     if _if(r1):
#         if _if(r2):
#             _.x = 0
#         if _else():
#             _.x = 1
#         _endif()
#     if _else():
#         _.x = 1
#     _endif()
#
#     return _.x


# @snark
# def comparisons(x):
# 	print(x)
# 	if x.value == 1 or x.value == 0:
# 		return 0
# 	return x-1 + comparisons(x-1)


# @snark
def checkOnes(x, y):
	"""
	Checks if any of the factors in y = 1
	"""
	_ = BranchingValues()

	_.x = 1

	for i in _range(len(y)):
		if _if(y[i][0] == 1):
			_.x = 0
		_endif()
		if _if(y[i][1] == 1):
			_.x = 0
		_endif()
	_endfor()

	return _.x


# @snark
def checkEqual(x, y):
	"""
	Checks if x(pubVal) and y(PubVal) are equal
	"""
	_ = BranchingValues()

	r1 = (x == y)
	_.x = 0
	if _if(r1):
		_.x = 1
	#if _else():
	#	_.x = 0
	_endif()

	return _.x

@snark
def votes(x, y):
	"""
	Function to prove that candidate got most votes

	x = [productOfPuzzles, numberOfVoters]			#public inputs
	y = [(voter1Factors), (voter2Favtors), ...]		#private inputs

	returns 0 if true, 1 if failed
	"""

	#TODO: y is currently public too because my_runtime broke the branching
	#That needs to be checked

	start_time = time.process_time()
	prodPuzzles = x[0]
	numVoters = x[1]
	voteFactors = y

	_ = BranchingValues()

	#CHECK NUMBER OF VOTES
	_.v1 = 0
	r1 = (len(y) > numVoters//2)
	if _if(r1):
		_.v1 = 1
	_endif()


	#CHECK FOR DUPLICATES

	val = 0
	_.v2 = 0

	# #TODO: The ifs inside for are causing unreachable code, and _breakif doesn't seem to work
	# for i in _range(0, len(y)-1, max = len(y)-1):
	# 	for j in _range(i+1, len(y), max = len(y)):
	# 		print(y[i], y[j])
	# 		val = tuple_compare(y[i], y[j])
	# 		_.v2 = val
	# 		_breakif(val == 0)
	# 	val = _.v2
	# 	_breakif(val == 0)
	# print('out')

	#Inefficient code with sum instead of breaking
	
	#if _if(len(y) > 1):
	for i in _range(len(y)-1, max = len(y)-1):
		for j in _range(i+1, len(y), max = len(y)):
			# print(y[i], y[j])
			val += tuple_compare(y[i], y[j])
		_endfor()
	_endfor()
	#_endif()

	_.v2 = checkEqual(0, val)




	#COMPUTE REMAINDER

	#Compute product of factors
	prod = 1
	for i in range(len(y)):
		prod *= y[i][0]*y[i][1]

	#Manually computing remainder because my_runtime broke the branching
	if prod.value==0:
		raise ValueError("division by zero")
	quo = PrivVal(prodPuzzles.value//prod.value)
	rem = PrivVal(prodPuzzles.value-quo.value*prod.value)
	rem.assert_positive(prod.value.bit_length())

	#Check value of remainder, and set return value
	_.v3 = 0
	r1 = (rem == 0)
	if _if(r1):
		_.v3 = 1
	_endif()


	#CHECK FOR FACTORS WHICH ARE 1
	_.v4 = checkOnes(x, y)

	# print('v4', _.v4)
	# print(_.v1*_.v2*_.v3*_.v4)


	v = _.v1*_.v2*_.v3*_.v4

	v.assert_nonzero()
	end_time = time.process_time()
	return end_time - start_time

# #Divisible
# x = [96, 5]
# y = [(1,2),(3,4),(1,2)]

# #Not divisible
# x = [100, 5]
# y = [(1,2),(3,4),(1,2)]

# #Divisible
# x = [96, 5]
# y = [(1,1),(3,4),(2,2)]

# # Divisible
# x = [96, 5]
# y = [(3,3),(3,4),(2,2)]

# Divisible
# x = [96, 2]
# y = [(2,4), (2,2)]


def generate_inputs(numVoters, param):
	start_time = time.process_time()
	y = []
	prodPuzzles = 1
	unique_set = set()
	while(len(unique_set)!=numVoters):
		unique_set.add((generate_prime_number(8), generate_prime_number(param)))
	for i in range(numVoters):
		# print(i)
		y.append(unique_set.pop())
		prodPuzzles *= y[i][0]*y[i][1]
	# print('out')
	x = [prodPuzzles, numVoters]
	end_time = time.process_time()
	# print("Generate inputs CPU time: "+str(end_time - start_time))
	return x, y, (end_time - start_time)

#Process input
a = sys.argv[1]
b = sys.argv[2]
x = [int(i) for i in a.split("|")]
temp = b.split("|")
i = 0
y = []
while i < len(temp):
	y.append((int(temp[i]), int(temp[i+1])))
	i+=2

# print('out2')
print("x:", x)
print("y:",y)
votes(x, y)

# vk, proof, pubvals = backend.prove()
#
# print(type(pubvals))
# print(type(vk))
# print(type(proof))
#
# with open("pysnark_pubvals", "w") as f:
#     pubvals.write(f)
#
# # Sanity check if the proof is verifiable
# import libsnark.alt_bn128 as real_backend
# print(real_backend.zk_verifier_strong_IC(vk, pubvals, proof))
# print("Verification status = ", status)

'''
for i in range(8, 17, 2):
	print("Params (8, "+ str(i) + ", 10)")
	x, y, cpu_time = generate_inputs(10, i)
	print("CPU time for input generation: "+str(round(cpu_time*1000, 2)))

	cpu_times = []
	for j in range(10):
		votes_cpu_time = votes(x, y)
		cpu_times.append(votes_cpu_time)
	mean_cpu_time = statistics.mean(cpu_times)
	print("CPU time for vote function: "+str(round(mean_cpu_time*1000, 2)))


for i in range(2, 11, 2):
	print("Params (8, 8, "+ str(i) + ")")
	x, y, cpu_time = generate_inputs(8, i)
	print("CPU time for input generation: "+str(round(cpu_time*1000, 2)))

	cpu_times = []
	for j in range(10):
		votes_cpu_time = votes(x, y)
		cpu_times.append(votes_cpu_time)
	mean_cpu_time = statistics.mean(cpu_times)
	print("CPU time for vote function: "+str(round(mean_cpu_time*1000, 2)))
'''
