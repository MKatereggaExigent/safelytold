import hashlib,json
from dataclasses import dataclass
from collections.abc import Iterable
def canonical(v:object)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()
def sha256_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def chained_hash(prev:str,record:object)->str:return sha256_bytes(bytes.fromhex(prev)+canonical(record))
@dataclass(frozen=True,slots=True)
class MerkleProofStep:sibling:str;sibling_on_left:bool
def merkle_root(leaves:Iterable[str])->str:
 level=[bytes.fromhex(x) for x in leaves]
 if not level:return hashlib.sha256(b"").hexdigest()
 while len(level)>1:
  if len(level)%2:level.append(level[-1])
  level=[hashlib.sha256(level[i]+level[i+1]).digest() for i in range(0,len(level),2)]
 return level[0].hex()
def verify_proof(leaf:str,proof:Iterable[MerkleProofStep],root:str)->bool:
 cur=bytes.fromhex(leaf)
 for s in proof:
  sib=bytes.fromhex(s.sibling);cur=hashlib.sha256(sib+cur if s.sibling_on_left else cur+sib).digest()
 return cur.hex()==root
