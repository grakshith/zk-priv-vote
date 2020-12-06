import sys
import libsnark.alt_bn128 as backend
import bpython

zk_verify = backend.zk_verifier_strong_IC

def verify(vk, pubvals, proof):
    status = zk_verify(vk, pubvals, proof)
    print("Verification status: ", status)


if __name__=="__main__":
    vk_file = "pysnark_vk"
    proof_file = "pysnark_log"
    pubvals_file = "pysnark_pubvals"
    with open(vk_file, "r") as f:
        vk = backend.ZKVerificationKey_read(f)
    with open(proof_file, "r") as f:
        proof = backend.ZKProof_read(f)
    with open(pubvals_file, "r") as f:
        pubvals = backend.R1csPrimaryInput.read(f)
    print("Verification key: ", vk.str())
    print("Pubvals: ", pubvals.str())
    print("Proof: ", proof.str())
    verify(vk, pubvals, proof)
