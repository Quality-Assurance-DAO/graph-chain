"""Transaction model for Cardano blockchain."""

from datetime import datetime
from typing import List, Optional, Dict, Any


class TransactionInput:
    """Represents a transaction input (UTXO reference)."""
    
    def __init__(
        self,
        tx_hash: str,
        index: int,
        address: Optional[str] = None
    ):
        """
        Initialize a TransactionInput instance.
        
        Args:
            tx_hash: Hash of previous transaction
            index: Output index in previous transaction
            address: Address that owns the input (for display)
        """
        self.tx_hash = tx_hash
        self.index = index
        self.address = address
    
    def __repr__(self):
        return f"TransactionInput(tx={self.tx_hash[:16]}..., index={self.index})"
    
    def to_dict(self):
        """Convert input to dictionary representation."""
        return {
            'tx_hash': self.tx_hash,
            'index': self.index,
            'address': self.address,
        }


class TransactionOutput:
    """Represents a transaction output (address-value pair)."""
    
    def __init__(
        self,
        address: str,
        amount: int,
        assets: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a TransactionOutput instance.
        
        Args:
            address: Recipient Cardano address
            amount: Amount in Lovelace
            assets: Native tokens if any (optional)
        """
        if not address:
            raise ValueError("address is required")
        if amount < 0:
            raise ValueError("amount must be non-negative")
        
        self.address = address
        self.amount = amount
        self.assets = assets or {}
    
    def __repr__(self):
        return f"TransactionOutput(addr={self.address[:16]}..., amount={self.amount})"
    
    def to_dict(self):
        """Convert output to dictionary representation."""
        return {
            'address': self.address,
            'amount': self.amount,
            'assets': self.assets,
        }


class Transaction:
    """Represents a transaction on the Cardano blockchain."""
    
    def __init__(
        self,
        tx_hash: str,
        block_hash: str,
        block_height: int,
        inputs: List[TransactionInput],
        outputs: List[TransactionOutput],
        fee: Optional[int] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize a Transaction instance.
        
        Args:
            tx_hash: Unique transaction identifier
            block_hash: Block containing this transaction
            block_height: Block height for quick reference
            inputs: List of input references
            outputs: List of output address-value pairs
            fee: Transaction fee in Lovelace (optional)
            timestamp: Transaction timestamp (from block) (optional)
        """
        if not tx_hash:
            raise ValueError("tx_hash is required")
        if not block_hash:
            raise ValueError("block_hash is required")
        if not inputs:
            raise ValueError("inputs list cannot be empty")
        if not outputs:
            raise ValueError("outputs list cannot be empty")
        
        self.tx_hash = tx_hash
        self.block_hash = block_hash
        self.block_height = block_height
        self.inputs = inputs
        self.outputs = outputs
        self.fee = fee
        self.timestamp = timestamp
    
    def __repr__(self):
        return f"Transaction(hash={self.tx_hash[:16]}..., block={self.block_height})"
    
    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return False
        return self.tx_hash == other.tx_hash
    
    def __hash__(self):
        return hash(self.tx_hash)
    
    def to_dict(self):
        """Convert transaction to dictionary representation."""
        return {
            'tx_hash': self.tx_hash,
            'block_hash': self.block_hash,
            'block_height': self.block_height,
            'inputs': [inp.to_dict() for inp in self.inputs],
            'outputs': [out.to_dict() for out in self.outputs],
            'fee': self.fee,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
        }


