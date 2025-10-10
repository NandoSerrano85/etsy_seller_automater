"""
Packing Slip API Routes

Endpoints for generating packing slips from order data.
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import get_current_user
from server.src.services.packing_slip_generator import PackingSlipGenerator
from PyPDF2 import PdfMerger
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/packing-slip", tags=["Packing Slip"])


# Pydantic models for request/response
class Address(BaseModel):
    """Customer address model."""
    line1: str
    line2: str | None = None
    city: str
    state: str
    zip: str
    country: str = "USA"


class Customer(BaseModel):
    """Customer information model."""
    name: str
    email: str | None = None
    address: Address | str


class OrderItem(BaseModel):
    """Order item model."""
    name: str
    mockup_url: str | None = None
    quantity: int = Field(ge=1)
    price: float = Field(ge=0)


class PackingSlipRequest(BaseModel):
    """Request model for generating packing slip."""
    shop_name: str
    customer: Customer
    items: List[OrderItem]
    subtotal: float = Field(ge=0)
    shipping_cost: float = Field(ge=0)
    total: float = Field(ge=0)
    order_number: str | None = None
    order_date: str | None = None


@router.post("/generate")
async def generate_packing_slip(
    request: PackingSlipRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a packing slip PDF from order data.

    Args:
        request: Packing slip request with order details
        current_user: Authenticated user
        db: Database session

    Returns:
        StreamingResponse: PDF file download
    """
    try:
        logger.info(f"Generating packing slip for order {request.order_number}")

        # Convert request to dict
        order_data = request.model_dump()

        # Generate packing slip
        generator = PackingSlipGenerator()
        pdf_bytes = generator.generate_packing_slip(order_data)

        # Create streaming response
        pdf_buffer = io.BytesIO(pdf_bytes)

        filename = f"packing_slip_{request.order_number or 'order'}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error generating packing slip: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate packing slip: {str(e)}"
        )


@router.post("/preview")
async def preview_packing_slip(
    request: PackingSlipRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a packing slip PDF preview (inline view).

    Args:
        request: Packing slip request with order details
        current_user: Authenticated user
        db: Database session

    Returns:
        StreamingResponse: PDF file for inline viewing
    """
    try:
        logger.info(f"Generating packing slip preview for order {request.order_number}")

        # Convert request to dict
        order_data = request.model_dump()

        # Generate packing slip
        generator = PackingSlipGenerator()
        pdf_bytes = generator.generate_packing_slip(order_data)

        # Create streaming response
        pdf_buffer = io.BytesIO(pdf_bytes)

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline"
            }
        )

    except Exception as e:
        logger.error(f"Error generating packing slip preview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate packing slip preview: {str(e)}"
        )


@router.get("/sample")
async def generate_sample_packing_slip():
    """
    Generate a sample packing slip for testing (no authentication required).

    Returns:
        StreamingResponse: Sample PDF file
    """
    try:
        from datetime import datetime

        sample_order = {
            "shop_name": "Funny Bunny Transfers",
            "order_number": "SAMPLE-12345",
            "order_date": datetime.now().strftime("%B %d, %Y"),
            "customer": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "address": {
                    "line1": "123 Main Street",
                    "line2": "Apt 4B",
                    "city": "New York",
                    "state": "NY",
                    "zip": "10001",
                    "country": "USA"
                }
            },
            "items": [
                {
                    "name": "Custom T-Shirt Design - Funny Bunny Logo",
                    "mockup_url": "https://via.placeholder.com/300/FF6B6B/FFFFFF?text=T-Shirt",
                    "quantity": 2,
                    "price": 24.99
                },
                {
                    "name": "Hoodie with Custom Transfer",
                    "mockup_url": "https://via.placeholder.com/300/4ECDC4/FFFFFF?text=Hoodie",
                    "quantity": 1,
                    "price": 39.99
                },
                {
                    "name": "Coffee Mug - Bunny Design",
                    "mockup_url": "https://via.placeholder.com/300/95E1D3/000000?text=Mug",
                    "quantity": 3,
                    "price": 14.99
                },
                {
                    "name": "Tote Bag - Canvas Print",
                    "mockup_url": "https://via.placeholder.com/300/F38181/FFFFFF?text=Tote",
                    "quantity": 1,
                    "price": 19.99
                }
            ],
            "subtotal": 139.93,
            "shipping_cost": 8.50,
            "total": 148.43
        }

        generator = PackingSlipGenerator()
        pdf_bytes = generator.generate_packing_slip(sample_order)

        pdf_buffer = io.BytesIO(pdf_bytes)

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=sample_packing_slip.pdf"
            }
        )

    except Exception as e:
        logger.error(f"Error generating sample packing slip: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sample packing slip: {str(e)}"
        )


@router.get("/bulk/etsy-orders")
async def generate_bulk_etsy_packing_slips(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate packing slips for all active Etsy orders and combine into a single PDF.

    Returns:
        StreamingResponse: Combined PDF with all packing slips
    """
    try:
        logger.info(f"Generating bulk packing slips for Etsy orders - User: {current_user.user_id}")

        # Import Etsy client
        from server.src.utils.etsy_client import EtsyClient
        from server.src.entities.etsy_store import EtsyStore
        from datetime import datetime

        # Get user's Etsy store
        user_id = current_user.get_uuid()
        etsy_store = db.query(EtsyStore).filter(
            EtsyStore.user_id == user_id,
            EtsyStore.is_active == True
        ).first()

        if not etsy_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Etsy store found for this user"
            )

        # Fetch active orders from Etsy
        etsy_client = EtsyClient(db)

        # Get receipts (orders) that need to be fulfilled
        # Status: open, unshipped, or awaiting_shipment
        receipts = etsy_client.get_shop_receipts(
            shop_id=etsy_store.etsy_shop_id,
            was_shipped=False,
            limit=100
        )

        if not receipts or len(receipts) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active orders found to generate packing slips"
            )

        logger.info(f"Found {len(receipts)} active Etsy orders")

        # Generate packing slip for each order
        generator = PackingSlipGenerator()
        pdf_merger = PdfMerger()

        for receipt in receipts:
            try:
                # Convert Etsy receipt to packing slip format
                order_data = _convert_etsy_receipt_to_packing_slip(receipt, etsy_store.shop_name)

                # Generate packing slip
                pdf_bytes = generator.generate_packing_slip(order_data)

                # Add to merger
                pdf_buffer = io.BytesIO(pdf_bytes)
                pdf_merger.append(pdf_buffer)

            except Exception as e:
                logger.error(f"Error generating packing slip for receipt {receipt.get('receipt_id')}: {e}")
                # Continue with other orders
                continue

        # Merge all PDFs
        output_buffer = io.BytesIO()
        pdf_merger.write(output_buffer)
        pdf_merger.close()
        output_buffer.seek(0)

        filename = f"packing_slips_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        logger.info(f"Successfully generated {len(receipts)} packing slips")

        return StreamingResponse(
            output_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating bulk packing slips: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bulk packing slips: {str(e)}"
        )


def _convert_etsy_receipt_to_packing_slip(receipt: Dict[str, Any], shop_name: str) -> Dict[str, Any]:
    """
    Convert an Etsy receipt to packing slip format.

    Args:
        receipt: Etsy receipt data
        shop_name: Shop name from Etsy store

    Returns:
        Dict formatted for packing slip generator
    """
    from datetime import datetime

    # Extract customer information
    buyer_name = f"{receipt.get('name', 'Customer')}"
    buyer_email = receipt.get('buyer_email', '')

    # Format shipping address
    shipping_address = {
        "line1": receipt.get('first_line', ''),
        "line2": receipt.get('second_line', ''),
        "city": receipt.get('city', ''),
        "state": receipt.get('state', ''),
        "zip": receipt.get('zip', ''),
        "country": receipt.get('country_iso', 'US')
    }

    # Extract order items
    items = []
    transactions = receipt.get('transactions', [])

    for transaction in transactions:
        # Get listing information
        listing = transaction.get('listing', {})

        # Try to get mockup image from listing
        mockup_url = None
        images = listing.get('images', [])
        if images and len(images) > 0:
            mockup_url = images[0].get('url_570xN') or images[0].get('url_fullxfull')

        items.append({
            "name": transaction.get('title', 'Product'),
            "mockup_url": mockup_url,
            "quantity": transaction.get('quantity', 1),
            "price": float(transaction.get('price', {}).get('amount', 0) / transaction.get('price', {}).get('divisor', 100))
        })

    # Calculate totals
    subtotal = float(receipt.get('subtotal', {}).get('amount', 0) / receipt.get('subtotal', {}).get('divisor', 100))
    shipping_cost = float(receipt.get('total_shipping_cost', {}).get('amount', 0) / receipt.get('total_shipping_cost', {}).get('divisor', 100))
    total = float(receipt.get('grandtotal', {}).get('amount', 0) / receipt.get('grandtotal', {}).get('divisor', 100))

    # Format order date
    order_date = ""
    if receipt.get('create_timestamp'):
        try:
            dt = datetime.fromtimestamp(receipt['create_timestamp'])
            order_date = dt.strftime("%B %d, %Y")
        except:
            pass

    return {
        "shop_name": shop_name,
        "order_number": str(receipt.get('receipt_id', '')),
        "order_date": order_date,
        "customer": {
            "name": buyer_name,
            "email": buyer_email,
            "address": shipping_address
        },
        "items": items,
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "total": total
    }
