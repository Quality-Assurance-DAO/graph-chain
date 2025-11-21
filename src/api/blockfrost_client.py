"""Blockfrost API client for Cardano blockchain data."""

from typing import List, Dict, Any, Optional
from blockfrost import BlockFrostApi, ApiError
from blockfrost.api.cardano.blocks import BlockResponse
from blockfrost.api.cardano.transactions import TransactionResponse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import MAX_RETRIES, RATE_LIMIT_BACKOFF


class BlockfrostClient:
    """Client for interacting with Blockfrost Cardano API."""
    
    def __init__(self, api_key: str, network: str = 'testnet'):
        """
        Initialize Blockfrost client.
        
        Args:
            api_key: Blockfrost API key
            network: Network to use ('testnet' or 'mainnet')
        """
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.network = network
        
        # Initialize Blockfrost API client
        if network == 'testnet':
            self.api = BlockFrostApi(
                project_id=api_key,
                base_url='https://cardano-testnet.blockfrost.io/api/v0'
            )
        else:
            self.api = BlockFrostApi(
                project_id=api_key,
                base_url='https://cardano-mainnet.blockfrost.io/api/v0'
            )
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RATE_LIMIT_BACKOFF, min=1, max=30),
        retry=retry_if_exception_type((ApiError, Exception)),
        reraise=True
    )
    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest block from the blockchain with exponential backoff retry.
        
        Returns:
            Dictionary containing block data, or None if error occurs
        """
        try:
            block = self.api.blocks_latest()
            return self._block_to_dict(block)
        except ApiError as e:
            # Check for rate limit (429)
            if hasattr(e, 'status_code') and e.status_code == 429:
                print(f"Rate limit hit: {e}")
                raise  # Re-raise to trigger retry with backoff
            print(f"API error fetching latest block: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error fetching latest block: {e}")
            raise
    
    def get_block_by_height(self, height: int) -> Optional[Dict[str, Any]]:
        """
        Get a block by its height.
        
        Args:
            height: Block height
            
        Returns:
            Dictionary containing block data, or None if error occurs
        """
        try:
            block = self.api.blocks(height=height)
            return self._block_to_dict(block)
        except ApiError as e:
            print(f"Error fetching block {height}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching block {height}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RATE_LIMIT_BACKOFF, min=1, max=30),
        retry=retry_if_exception_type((ApiError, Exception)),
        reraise=True
    )
    def get_block_transactions(self, block_hash: str) -> List[Dict[str, Any]]:
        """
        Get all transactions in a block.
        
        Args:
            block_hash: Hash of the block
            
        Returns:
            List of transaction dictionaries
        """
        try:
            # Get all transactions for the block
            transactions = self.api.blocks_transactions_all(hash_or_number=block_hash)
            result = []
            for tx in transactions:
                tx_dict = self._transaction_to_dict(tx)
                # Fetch detailed transaction info including inputs/outputs
                try:
                    tx_details = self.api.transaction(tx.hash)
                    tx_dict['inputs'] = self._get_transaction_inputs(tx.hash)
                    tx_dict['outputs'] = self._get_transaction_outputs(tx.hash)
                except Exception:
                    # If detailed fetch fails, continue with basic info
                    pass
                result.append(tx_dict)
            return result
        except ApiError as e:
            # Check for rate limit (429)
            if hasattr(e, 'status_code') and e.status_code == 429:
                print(f"Rate limit hit fetching transactions: {e}")
                raise  # Re-raise to trigger retry with backoff
            print(f"API error fetching transactions for block {block_hash}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error fetching transactions: {e}")
            raise
    
    def _get_transaction_inputs(self, tx_hash: str) -> List[Dict[str, Any]]:
        """Get transaction inputs (UTXOs)."""
        try:
            utxos = self.api.transaction_utxos(tx_hash)
            inputs = []
            for utxo in utxos.inputs:
                inputs.append({
                    'tx_hash': utxo.tx_hash,
                    'index': utxo.output_index,
                    'address': utxo.address,
                })
            return inputs
        except Exception:
            return []
    
    def _get_transaction_outputs(self, tx_hash: str) -> List[Dict[str, Any]]:
        """Get transaction outputs."""
        try:
            utxos = self.api.transaction_utxos(tx_hash)
            outputs = []
            for utxo in utxos.outputs:
                amount = 0
                if utxo.amount:
                    # Find ADA amount (lovelace)
                    for amt in utxo.amount:
                        if amt.unit == 'lovelace':
                            amount = int(amt.quantity)
                            break
                outputs.append({
                    'address': utxo.address,
                    'amount': amount,
                    'assets': {},  # Could parse native tokens here if needed
                })
            return outputs
        except Exception:
            return []
    
    def _block_to_dict(self, block: BlockResponse) -> Dict[str, Any]:
        """Convert Blockfrost BlockResponse to dictionary."""
        return {
            'hash': block.hash,
            'height': block.height,
            'time': block.time,
            'slot': getattr(block, 'slot', None),
            'tx_count': getattr(block, 'tx_count', None),
        }
    
    def _transaction_to_dict(self, tx: TransactionResponse) -> Dict[str, Any]:
        """Convert Blockfrost TransactionResponse to dictionary."""
        return {
            'hash': tx.hash,
            'block': getattr(tx, 'block', None),
            'block_height': getattr(tx, 'block_height', None),
            'slot': getattr(tx, 'slot', None),
            'index': getattr(tx, 'index', None),
            'fee': getattr(tx, 'fee', None),
            'deposit': getattr(tx, 'deposit', None),
            'size': getattr(tx, 'size', None),
            'invalid_before': getattr(tx, 'invalid_before', None),
            'invalid_hereafter': getattr(tx, 'invalid_hereafter', None),
        }

