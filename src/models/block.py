"""Block model for Cardano blockchain."""

from datetime import datetime
from typing import Optional


class Block:
    """Represents a block on the Cardano blockchain."""
    
    def __init__(
        self,
        block_hash: str,
        block_height: int,
        timestamp: datetime,
        slot: Optional[int] = None,
        tx_count: Optional[int] = None
    ):
        """
        Initialize a Block instance.
        
        Args:
            block_hash: Unique identifier for the block
            block_height: Block number/height in the blockchain
            timestamp: When the block was created
            slot: Cardano slot number (optional)
            tx_count: Number of transactions in the block (optional)
        """
        if not block_hash:
            raise ValueError("block_hash is required")
        if block_height < 0:
            raise ValueError("block_height must be non-negative")
        
        self.block_hash = block_hash
        self.block_height = block_height
        self.timestamp = timestamp
        self.slot = slot
        self.tx_count = tx_count
    
    def __repr__(self):
        return f"Block(hash={self.block_hash[:16]}..., height={self.block_height})"
    
    def __eq__(self, other):
        if not isinstance(other, Block):
            return False
        return self.block_hash == other.block_hash
    
    def __hash__(self):
        return hash(self.block_hash)
    
    def to_dict(self):
        """Convert block to dictionary representation."""
        return {
            'block_hash': self.block_hash,
            'block_height': self.block_height,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'slot': self.slot,
            'tx_count': self.tx_count,
        }


