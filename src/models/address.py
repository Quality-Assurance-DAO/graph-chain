"""Address model for Cardano blockchain."""

from datetime import datetime
from typing import Optional


class Address:
    """Represents a Cardano address that can send or receive value."""
    
    def __init__(
        self,
        address: str,
        first_seen: Optional[datetime] = None,
        total_received: Optional[int] = None,
        total_sent: Optional[int] = None,
        transaction_count: Optional[int] = None
    ):
        """
        Initialize an Address instance.
        
        Args:
            address: Cardano address (Bech32 format)
            first_seen: When address first appeared in graph (optional)
            total_received: Cumulative Lovelace received (optional)
            total_sent: Cumulative Lovelace sent (optional)
            transaction_count: Number of transactions involving this address (optional)
        """
        if not address:
            raise ValueError("address is required")
        
        self.address = address
        self.first_seen = first_seen
        self.total_received = total_received or 0
        self.total_sent = total_sent or 0
        self.transaction_count = transaction_count or 0
    
    def __repr__(self):
        return f"Address(addr={self.address[:16]}..., tx_count={self.transaction_count})"
    
    def __eq__(self, other):
        if not isinstance(other, Address):
            return False
        return self.address == other.address
    
    def __hash__(self):
        return hash(self.address)
    
    def update_stats(self, received: int = 0, sent: int = 0):
        """
        Update address statistics.
        
        Args:
            received: Amount received in this transaction
            sent: Amount sent in this transaction
        """
        self.total_received += received
        self.total_sent += sent
        self.transaction_count += 1
    
    def to_dict(self):
        """Convert address to dictionary representation."""
        return {
            'address': self.address,
            'first_seen': self.first_seen.isoformat() if isinstance(self.first_seen, datetime) else self.first_seen,
            'total_received': self.total_received,
            'total_sent': self.total_sent,
            'transaction_count': self.transaction_count,
        }

