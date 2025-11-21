"""Data fetcher for polling Cardano blockchain data."""

import time
import logging
from datetime import datetime
from typing import Optional, List
from src.api.blockfrost_client import BlockfrostClient
from src.models import Block, Transaction, TransactionInput, TransactionOutput, Address
from src.graph_builder import GraphBuilder
from src.config import BLOCKFROST_API_KEY, POLLING_INTERVAL, validate_config
from blockfrost import ApiError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches blockchain data and updates the graph."""
    
    def __init__(self, graph_builder: GraphBuilder, api_client: Optional[BlockfrostClient] = None):
        """
        Initialize DataFetcher.
        
        Args:
            graph_builder: GraphBuilder instance to update
            api_client: BlockfrostClient instance (creates new one if not provided)
        """
        validate_config()
        
        self.graph_builder = graph_builder
        self.api_client = api_client or BlockfrostClient(BLOCKFROST_API_KEY, network='testnet')
        self.running = False
        self.last_block_height: Optional[int] = None
        self.polling_interval = POLLING_INTERVAL
        
        # Status tracking (T036)
        self.api_status = 'connected'
        self.polling_status = 'stopped'
        self.rate_limit_status = {'limited': False, 'retry_after': None}
        self.error_state = None
        self.last_block_fetched: Optional[datetime] = None
        self.consecutive_errors = 0
    
    def parse_block(self, block_data: dict) -> Block:
        """
        Parse Blockfrost API block response into Block model.
        
        Args:
            block_data: Dictionary from Blockfrost API
            
        Returns:
            Block instance
        """
        # Parse timestamp
        timestamp_str = block_data.get('time')
        if isinstance(timestamp_str, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        return Block(
            block_hash=block_data['hash'],
            block_height=block_data['height'],
            timestamp=timestamp,
            slot=block_data.get('slot'),
            tx_count=block_data.get('tx_count'),
        )
    
    def parse_transaction(self, tx_data: dict, block_hash: str, block_height: int) -> Transaction:
        """
        Parse Blockfrost API transaction response into Transaction model.
        
        Args:
            tx_data: Dictionary from Blockfrost API
            block_hash: Hash of the containing block
            block_height: Height of the containing block
            
        Returns:
            Transaction instance
        """
        # Parse inputs
        inputs = []
        for inp_data in tx_data.get('inputs', []):
            inputs.append(TransactionInput(
                tx_hash=inp_data.get('tx_hash', ''),
                index=inp_data.get('index', 0),
                address=inp_data.get('address'),
            ))
        
        # Parse outputs
        outputs = []
        for out_data in tx_data.get('outputs', []):
            outputs.append(TransactionOutput(
                address=out_data.get('address', ''),
                amount=out_data.get('amount', 0),
                assets=out_data.get('assets', {}),
            ))
        
        return Transaction(
            tx_hash=tx_data['hash'],
            block_hash=block_hash,
            block_height=block_height,
            inputs=inputs,
            outputs=outputs,
            fee=tx_data.get('fee'),
            timestamp=None,  # Will be set from block timestamp if needed
        )
    
    def fetch_and_update(self) -> bool:
        """
        Fetch latest block and update graph with error handling.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Reset error state on successful attempt
            self.consecutive_errors = 0
            self.error_state = None
            self.api_status = 'connected'
            self.rate_limit_status = {'limited': False, 'retry_after': None}
            
            # Get latest block (with retry logic from client)
            block_data = self.api_client.get_latest_block()
            if not block_data:
                self.api_status = 'disconnected'
                return False
            
            block = self.parse_block(block_data)
            
            # Skip if we've already processed this block
            if self.last_block_height is not None and block.block_height <= self.last_block_height:
                return True  # Not an error, just no new data
            
            # Add block to graph
            self.graph_builder.add_block(block)
            
            # Fetch and process transactions
            transactions_data = self.api_client.get_block_transactions(block.block_hash)
            for tx_data in transactions_data:
                try:
                    transaction = self.parse_transaction(tx_data, block.block_hash, block.block_height)
                    self.graph_builder.add_transaction(transaction)
                    
                    # Add addresses from transaction
                    for inp in transaction.inputs:
                        if inp.address:
                            address = Address(
                                address=inp.address,
                                first_seen=block.timestamp,
                            )
                            self.graph_builder.add_address(address)
                    
                    for out in transaction.outputs:
                        address = Address(
                            address=out.address,
                            first_seen=block.timestamp,
                        )
                        # Update address stats
                        address.update_stats(received=out.amount)
                        self.graph_builder.add_address(address)
                except Exception as e:
                    logger.warning(f"Error parsing transaction: {e}")
                    continue
            
            self.last_block_height = block.block_height
            self.last_block_fetched = datetime.now()
            return True
            
        except ApiError as e:
            # Handle API errors (T034, T035)
            self.consecutive_errors += 1
            error_msg = str(e)
            
            # Check for rate limit (429)
            if hasattr(e, 'status_code') and e.status_code == 429:
                self.rate_limit_status = {
                    'limited': True,
                    'retry_after': 30  # Estimate 30 seconds
                }
                self.api_status = 'rate_limited'
                logger.warning(f"Rate limit hit: {e}. Pausing polling.")
                # Pause polling for backoff period
                time.sleep(30)
                return False
            else:
                self.api_status = 'disconnected'
                self.error_state = error_msg
                logger.error(f"API error: {e}")
                # Continue polling loop without crashing (T039)
                return False
                
        except Exception as e:
            # Handle unexpected errors (T034)
            self.consecutive_errors += 1
            self.error_state = str(e)
            self.api_status = 'disconnected'
            logger.error(f"Unexpected error in fetch_and_update: {e}")
            # Continue polling loop without crashing (T039)
            return False
    
    def start_polling(self):
        """Start polling loop in background thread with error handling."""
        self.running = True
        self.polling_status = 'active'
        
        while self.running:
            try:
                success = self.fetch_and_update()
                
                # Adjust polling interval based on rate limit status
                if self.rate_limit_status.get('limited'):
                    sleep_time = self.rate_limit_status.get('retry_after', 30)
                    logger.info(f"Rate limited. Waiting {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    self.rate_limit_status = {'limited': False, 'retry_after': None}
                else:
                    time.sleep(self.polling_interval)
                    
            except KeyboardInterrupt:
                logger.info("Polling interrupted by user")
                break
            except Exception as e:
                logger.error(f"Critical error in polling loop: {e}")
                # Continue loop to attempt recovery
                time.sleep(self.polling_interval * 2)  # Longer wait on critical errors
    
    def stop_polling(self):
        """Stop polling loop."""
        self.running = False
        self.polling_status = 'stopped'
    
    def get_status(self) -> dict:
        """Get current status information."""
        return {
            'api_status': self.api_status,
            'polling_status': self.polling_status,
            'rate_limit_status': self.rate_limit_status,
            'error_state': self.error_state,
            'last_block_fetched': self.last_block_fetched.isoformat() if self.last_block_fetched else None,
            'consecutive_errors': self.consecutive_errors,
        }

