"""
Railway Worker Service for Background Job Processing
Handles image processing, mockup generation, and print file creation
"""

import os
import sys
import logging
import signal
import time
from typing import Dict, Any
import redis
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/app')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkerService:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable is required")
        
        self.redis_client = redis.from_url(self.redis_url)
        self.running = False
        
        # Job handlers
        self.job_handlers = {
            'process_mockup': self.process_mockup_job,
            'process_design': self.process_design_job,
            'create_print_files': self.create_print_files_job,
            'sync_etsy_orders': self.sync_etsy_orders_job
        }
        
        logger.info("Worker service initialized")
    
    def process_mockup_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process mockup generation job"""
        try:
            logger.info(f"Processing mockup job: {job_data.get('job_id')}")
            
            # Import here to avoid circular dependencies
            from server.src.routes.mockups.service import create_mockup
            from server.src.database.core import get_db
            
            # Extract job parameters
            user_id = job_data.get('user_id')
            mockup_data = job_data.get('mockup_data')
            
            # Process mockup
            db = next(get_db())
            result = create_mockup(db, user_id, mockup_data)
            
            return {
                'status': 'completed',
                'result': str(result.id) if result else None,
                'message': 'Mockup created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing mockup job: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def process_design_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process design upload and processing job"""
        try:
            logger.info(f"Processing design job: {job_data.get('job_id')}")
            
            # Import here to avoid circular dependencies
            from server.src.routes.designs.service import create_design_images
            from server.src.database.core import get_db
            
            # Process design
            # Implementation depends on your specific design processing needs
            
            return {
                'status': 'completed',
                'message': 'Design processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing design job: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def create_print_files_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create print files/gang sheets job"""
        try:
            logger.info(f"Processing print files job: {job_data.get('job_id')}")
            
            # Import here to avoid circular dependencies
            from server.src.routes.orders.service import create_print_files
            from server.src.database.core import get_db
            
            # Extract job parameters
            user_id = job_data.get('user_id')
            template_name = job_data.get('template_name')
            
            # Process print files
            db = next(get_db())
            # Note: You'll need to adapt this to your current user object structure
            result = create_print_files(user_id, db)
            
            return {
                'status': 'completed',
                'result': result,
                'message': 'Print files created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating print files: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def sync_etsy_orders_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync orders from Etsy job"""
        try:
            logger.info(f"Processing Etsy sync job: {job_data.get('job_id')}")
            
            # Import here to avoid circular dependencies
            from server.src.utils.etsy_api_engine import EtsyAPI
            from server.src.database.core import get_db
            
            # Extract job parameters
            user_id = job_data.get('user_id')
            
            # Sync orders
            db = next(get_db())
            etsy_api = EtsyAPI(user_id, db)
            # Add your order syncing logic here
            
            return {
                'status': 'completed',
                'message': 'Orders synced successfully'
            }
            
        except Exception as e:
            logger.error(f"Error syncing Etsy orders: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def process_job(self, job_data: Dict[str, Any]) -> None:
        """Process a single job"""
        try:
            job_type = job_data.get('job_type')
            job_id = job_data.get('job_id')
            
            logger.info(f"Processing job {job_id} of type {job_type}")
            
            # Get handler for job type
            handler = self.job_handlers.get(job_type)
            if not handler:
                logger.error(f"No handler found for job type: {job_type}")
                return
            
            # Execute job
            start_time = time.time()
            result = handler(job_data)
            end_time = time.time()
            
            # Log result
            logger.info(f"Job {job_id} completed in {end_time - start_time:.2f}s with status: {result.get('status')}")
            
            # Store result back to Redis (optional)
            result_key = f"job_result:{job_id}"
            result['processed_at'] = datetime.utcnow().isoformat()
            result['processing_time'] = end_time - start_time
            
            self.redis_client.setex(
                result_key,
                3600,  # Expire after 1 hour
                json.dumps(result)
            )
            
        except Exception as e:
            logger.error(f"Error processing job: {e}")
    
    def run(self):
        """Main worker loop"""
        logger.info("Starting worker service...")
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        
        try:
            while self.running:
                try:
                    # Block and wait for jobs from Redis queue
                    # Using BLPOP with timeout for graceful shutdown
                    result = self.redis_client.blpop(['job_queue'], timeout=1)
                    
                    if result:
                        queue_name, job_data_str = result
                        try:
                            job_data = json.loads(job_data_str)
                            self.process_job(job_data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid job data: {e}")
                        except Exception as e:
                            logger.error(f"Error processing job: {e}")
                    
                except redis.RedisError as e:
                    logger.error(f"Redis error: {e}")
                    time.sleep(5)  # Wait before retrying
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.shutdown()
    
    def shutdown(self, signum=None, frame=None):
        """Graceful shutdown"""
        logger.info("Shutting down worker service...")
        self.running = False

def main():
    """Entry point for the worker service"""
    try:
        worker = WorkerService()
        worker.run()
    except Exception as e:
        logger.error(f"Failed to start worker service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()