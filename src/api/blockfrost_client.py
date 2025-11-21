"""Blockfrost API client for Cardano blockchain data."""

from typing import List, Dict, Any, Optional
from blockfrost import BlockFrostApi, ApiError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import MAX_RETRIES, RATE_LIMIT_BACKOFF


class BlockfrostClient:
    """Client for interacting with Blockfrost Cardano API."""
    
    def __init__(self, api_key: str, network: str = 'mainnet'):
        """
        Initialize Blockfrost client.
        
        Args:
            api_key: Blockfrost API key
            network: Network to use ('mainnet', 'preview', or 'preprod')
                    Note: 'testnet' is decommissioned, use 'preview' or 'preprod' instead
        """
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.network = network
        
        # Initialize Blockfrost API client
        # Note: Blockfrost library automatically adds /v0, so base_url should end at /api
        network_urls = {
            'mainnet': 'https://cardano-mainnet.blockfrost.io/api',
            'preview': 'https://cardano-preview.blockfrost.io/api',
            'preprod': 'https://cardano-preprod.blockfrost.io/api',
            'testnet': 'https://cardano-testnet.blockfrost.io/api',  # Deprecated but kept for compatibility
        }
        
        if network not in network_urls:
            raise ValueError(
                f"Invalid network '{network}'. "
                f"Supported networks: {', '.join(network_urls.keys())}"
            )
        
        base_url = network_urls[network]
        if network == 'testnet':
            print("WARNING: Cardano testnet has been decommissioned. Consider using 'preview' or 'preprod' instead.")
        
        # Initialize Blockfrost API client
        # The library automatically appends /v0 to the base_url
        self.api = BlockFrostApi(
            project_id=api_key,
            base_url=base_url
        )
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RATE_LIMIT_BACKOFF, min=1, max=30),
        retry=retry_if_exception_type((ApiError,)),
        reraise=True
    )
    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest block from the blockchain with exponential backoff retry.
        
        Returns:
            Dictionary containing block data, or None if error occurs
        """
        try:
            # Try to get block as JSON first (more reliable)
            try:
                block = self.api.block_latest(return_type='json')
                # If it's already a dict, check if it's an error response
                if isinstance(block, dict):
                    # Check for API error responses
                    if 'error' in block or 'status_code' in block or 'message' in block:
                        error_msg = block.get('message') or block.get('error', 'Unknown API error')
                        print(f"API error response: {error_msg}")
                        raise ApiError(f"API returned error: {error_msg}")
                    
                    # Validate it has required block fields
                    if not block.get('hash') or block.get('height') is None:
                        print(f"Invalid block data received: {block}")
                        return None
                    return block
            except ApiError:
                # Re-raise API errors to trigger retry
                raise
            except Exception:
                # Fall back to object mode for other exceptions
                pass
            
            # Try object mode
            block = self.api.block_latest()
            if block is None:
                print("API returned None for latest block")
                return None
            
            return self._block_to_dict(block)
        except ApiError as e:
            # ApiError has status_code, error, and message attributes
            error_status = getattr(e, 'status_code', None)
            error_message = getattr(e, 'message', str(e))
            error_type = getattr(e, 'error', 'Unknown')
            
            # Check for rate limit (429)
            if error_status == 429:
                print(f"Rate limit hit: {error_message}")
                raise  # Re-raise to trigger retry with backoff
            
            # For 400 errors (Bad Request), don't retry - likely a configuration issue
            if error_status == 400:
                print(f"Bad Request (400) - {error_type}: {error_message}")
                # Don't retry on 400 errors - return None instead to avoid infinite retries
                return None
            
            print(f"API error fetching latest block (status: {error_status}): {error_message}")
            raise
        except ValueError as e:
            # This is our validation error - log and return None
            print(f"Invalid block data: {e}")
            return None
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
            # Note: block_transactions returns a list of transaction hash strings, not objects
            transactions = self.api.block_transactions(hash_or_number=block_hash)
            result = []
            for tx in transactions:
                # Handle case where tx is a string (hash) or an object
                if isinstance(tx, str):
                    # tx is already a hash string
                    tx_hash = tx
                    tx_dict = {'hash': tx_hash}
                else:
                    # tx is an object, convert it
                    tx_dict = self._transaction_to_dict(tx)
                    tx_hash = tx_dict.get('hash') or getattr(tx, 'hash', None)
                
                # Skip if we don't have a hash
                if not tx_hash:
                    continue
                
                # Fetch detailed transaction info including inputs/outputs
                try:
                    tx_details = self.api.transaction(tx_hash)
                    tx_dict['inputs'] = self._get_transaction_inputs(tx_hash)
                    tx_dict['outputs'] = self._get_transaction_outputs(tx_hash)
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
    
    def _block_to_dict(self, block: Any) -> Dict[str, Any]:
        """Convert Blockfrost block object to dictionary."""
        if block is None:
            raise ValueError("Block object is None")
        
        # Try multiple ways to access the data
        block_hash = None
        block_height = None
        
        # Method 1: Try direct attribute access
        block_hash = getattr(block, 'hash', None)
        block_height = getattr(block, 'height', None)
        
        # Method 2: Try dictionary access if it's a dict-like object
        if not block_hash and hasattr(block, '__getitem__'):
            try:
                block_hash = block.get('hash') if hasattr(block, 'get') else block['hash']
                block_height = block.get('height') if hasattr(block, 'get') else block['height']
            except (KeyError, TypeError):
                pass
        
        # Method 3: Try converting to dict if possible
        if not block_hash and hasattr(block, '__dict__'):
            block_dict = block.__dict__
            block_hash = block_dict.get('hash')
            block_height = block_dict.get('height')
        
        # Validate that required fields exist
        if not block_hash:
            # Try to get more info about the block object for debugging
            block_type = type(block).__name__
            block_repr = str(block)[:200] if hasattr(block, '__str__') else 'N/A'
            available_attrs = [attr for attr in dir(block) if not attr.startswith('_')][:10]
            raise ValueError(
                f"Block object missing 'hash' attribute. "
                f"Type: {block_type}, "
                f"Available attributes: {available_attrs}, "
                f"Repr: {block_repr}"
            )
        if block_height is None:
            raise ValueError("Block object missing 'height' attribute")
        
        return {
            'hash': block_hash,
            'height': block_height,
            'time': getattr(block, 'time', None) or (block.get('time') if hasattr(block, 'get') else None),
            'slot': getattr(block, 'slot', None) or (block.get('slot') if hasattr(block, 'get') else None),
            'tx_count': getattr(block, 'tx_count', None) or (block.get('tx_count') if hasattr(block, 'get') else None),
        }
    
    def _transaction_to_dict(self, tx: Any) -> Dict[str, Any]:
        """Convert Blockfrost transaction object to dictionary."""
        return {
            'hash': getattr(tx, 'hash', None),
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

