"""
Packing Slip Generator Service

Generates professional packing slips for orders with:
- Shop name and customer information at the top
- Product mockup thumbnails in a grid layout
- Quantity displayed under each thumbnail
- Order summary table at the bottom
"""
import io
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas as pdf_canvas
import requests

logger = logging.getLogger(__name__)


class PackingSlipGenerator:
    """Generate packing slips for orders."""

    def __init__(self):
        self.page_width, self.page_height = letter  # 8.5" x 11"
        self.margin = 0.5 * inch
        self.content_width = self.page_width - (2 * self.margin)
        self.content_height = self.page_height - (2 * self.margin)
        self.thumbnail_spacing = 1 * inch
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles."""
        # Shop name style
        self.styles.add(ParagraphStyle(
            name='ShopName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))

        # Customer info style
        self.styles.add(ParagraphStyle(
            name='CustomerInfo',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#34495E')
        ))

        # Quantity style
        self.styles.add(ParagraphStyle(
            name='Quantity',
            parent=self.styles['Normal'],
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#E74C3C'),
            alignment=TA_CENTER
        ))

        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.white
        ))

    def generate_packing_slip(self, order_data: Dict[str, Any]) -> bytes:
        """
        Generate a packing slip PDF for an order.

        Args:
            order_data: Dictionary containing:
                - shop_name: str
                - customer: dict with name, address, email
                - items: list of dicts with mockup_url, quantity, name, price
                - subtotal: float
                - shipping_cost: float
                - total: float
                - order_number: str (optional)
                - order_date: str (optional)

        Returns:
            bytes: PDF file content
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )

        # Build story (content elements)
        story = []

        # Add header
        story.extend(self._create_header(order_data))

        # Add customer information
        story.extend(self._create_customer_info(order_data.get('customer', {})))

        story.append(Spacer(1, 0.3 * inch))

        # Add product grid
        story.extend(self._create_product_grid(order_data.get('items', [])))

        story.append(Spacer(1, 0.5 * inch))

        # Add order summary table
        story.extend(self._create_order_summary(order_data))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _create_header(self, order_data: Dict[str, Any]) -> List:
        """Create the header with shop name and order info."""
        elements = []

        # Shop name
        shop_name = order_data.get('shop_name', 'Your Shop')
        elements.append(Paragraph(shop_name, self.styles['ShopName']))

        # Order info
        order_info_text = "PACKING SLIP"
        if order_data.get('order_number'):
            order_info_text += f" - Order #{order_data['order_number']}"
        if order_data.get('order_date'):
            order_info_text += f" - {order_data['order_date']}"

        order_info_style = ParagraphStyle(
            name='OrderInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        elements.append(Paragraph(order_info_text, order_info_style))

        return elements

    def _create_customer_info(self, customer: Dict[str, Any]) -> List:
        """Create customer information section."""
        elements = []

        # Customer info header
        header_style = ParagraphStyle(
            name='InfoHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=8
        )
        elements.append(Paragraph("Ship To:", header_style))

        # Customer details
        customer_name = customer.get('name', 'N/A')
        email = customer.get('email', '')
        address = customer.get('address', {})

        # Format address
        address_lines = []
        if isinstance(address, dict):
            address_lines.append(address.get('line1', ''))
            if address.get('line2'):
                address_lines.append(address.get('line2', ''))
            city_state_zip = f"{address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}"
            address_lines.append(city_state_zip.strip())
            if address.get('country'):
                address_lines.append(address.get('country', ''))
        elif isinstance(address, str):
            address_lines = [address]

        customer_text = f"<b>{customer_name}</b><br/>"
        if email:
            customer_text += f"{email}<br/>"
        customer_text += "<br/>".join(filter(None, address_lines))

        elements.append(Paragraph(customer_text, self.styles['CustomerInfo']))

        return elements

    def _create_product_grid(self, items: List[Dict[str, Any]]) -> List:
        """Create a grid of product thumbnails with quantities."""
        elements = []

        if not items:
            return elements

        # Calculate grid dimensions
        thumbnail_size = 2.5 * inch  # Image size
        cell_width = thumbnail_size + (self.thumbnail_spacing / 2)
        columns = int(self.content_width / cell_width)
        columns = max(1, min(columns, 3))  # 1-3 columns

        # Organize items into grid rows
        rows = []
        current_row = []

        for item in items:
            if len(current_row) >= columns:
                rows.append(current_row)
                current_row = []

            # Create cell with image and quantity
            cell_content = self._create_product_cell(
                item.get('mockup_url'),
                item.get('quantity', 1),
                item.get('name', 'Product'),
                thumbnail_size
            )
            current_row.append(cell_content)

        # Add last row
        if current_row:
            # Fill remaining cells
            while len(current_row) < columns:
                current_row.append('')
            rows.append(current_row)

        # Create table
        if rows:
            table = Table(rows, colWidths=[cell_width] * columns)
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), self.thumbnail_spacing / 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), self.thumbnail_spacing / 4),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            elements.append(table)

        return elements

    def _create_product_cell(self, mockup_url: Optional[str], quantity: int,
                            product_name: str, size: float) -> List:
        """Create a cell with product image and quantity."""
        cell_elements = []

        # Add product image
        if mockup_url:
            try:
                img = self._get_image_from_url(mockup_url, size, size)
                if img:
                    cell_elements.append(img)
            except Exception as e:
                logger.error(f"Failed to load image from {mockup_url}: {e}")
                # Add placeholder
                cell_elements.append(Paragraph(
                    f"<i>{product_name[:30]}...</i>",
                    self.styles['Normal']
                ))
        else:
            # Placeholder text
            cell_elements.append(Paragraph(
                f"<i>{product_name[:30]}...</i>",
                self.styles['Normal']
            ))

        # Add spacing
        cell_elements.append(Spacer(1, 0.1 * inch))

        # Add quantity
        qty_text = f"<b>Qty: {quantity}</b>"
        cell_elements.append(Paragraph(qty_text, self.styles['Quantity']))

        return cell_elements

    def _get_image_from_url(self, url: str, width: float, height: float) -> Optional[Image]:
        """Download and create an Image object from URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            img_buffer = io.BytesIO(response.content)
            img = Image(img_buffer, width=width, height=height)
            return img
        except Exception as e:
            logger.error(f"Error loading image from {url}: {e}")
            return None

    def _create_order_summary(self, order_data: Dict[str, Any]) -> List:
        """Create order summary table at the bottom."""
        elements = []

        items = order_data.get('items', [])
        subtotal = order_data.get('subtotal', 0.0)
        shipping = order_data.get('shipping_cost', 0.0)
        total = order_data.get('total', 0.0)

        # Table header
        header_style = ParagraphStyle(
            name='SummaryHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=10
        )
        elements.append(Paragraph("Order Summary", header_style))

        # Create table data
        table_data = [
            [
                Paragraph('<b>Item</b>', self.styles['Normal']),
                Paragraph('<b>Quantity</b>', self.styles['Normal']),
                Paragraph('<b>Price</b>', self.styles['Normal']),
                Paragraph('<b>Total</b>', self.styles['Normal'])
            ]
        ]

        # Add items
        for item in items:
            name = item.get('name', 'Product')[:40]
            quantity = item.get('quantity', 1)
            price = item.get('price', 0.0)
            item_total = quantity * price

            table_data.append([
                Paragraph(name, self.styles['Normal']),
                Paragraph(str(quantity), self.styles['Normal']),
                Paragraph(f"${price:.2f}", self.styles['Normal']),
                Paragraph(f"${item_total:.2f}", self.styles['Normal'])
            ])

        # Add subtotal, shipping, total
        table_data.extend([
            ['', '', Paragraph('<b>Subtotal:</b>', self.styles['Normal']),
             Paragraph(f"<b>${subtotal:.2f}</b>", self.styles['Normal'])],
            ['', '', Paragraph('<b>Shipping:</b>', self.styles['Normal']),
             Paragraph(f"<b>${shipping:.2f}</b>", self.styles['Normal'])],
            ['', '', Paragraph('<b>Total:</b>', self.styles['Normal']),
             Paragraph(f"<b>${total:.2f}</b>", self.styles['Normal'])]
        ])

        # Create table
        table = Table(table_data, colWidths=[3.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),

            # Data rows
            ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -4), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -4), [colors.white, colors.HexColor('#F8F9FA')]),
            ('GRID', (0, 0), (-1, -4), 0.5, colors.HexColor('#BDC3C7')),

            # Summary rows (last 3)
            ('LINEABOVE', (2, -3), (-1, -3), 2, colors.HexColor('#34495E')),
            ('LINEABOVE', (2, -1), (-1, -1), 2, colors.HexColor('#34495E')),
            ('FONTSIZE', (0, -3), (-1, -1), 11),

            # Alignment
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))

        elements.append(table)

        return elements


# Example usage
def generate_sample_packing_slip():
    """Generate a sample packing slip for testing."""
    sample_order = {
        "shop_name": "Funny Bunny Transfers",
        "order_number": "ORD-12345",
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
                "name": "Custom T-Shirt Design",
                "mockup_url": "https://via.placeholder.com/300",
                "quantity": 2,
                "price": 24.99
            },
            {
                "name": "Hoodie with Logo",
                "mockup_url": "https://via.placeholder.com/300",
                "quantity": 1,
                "price": 39.99
            },
            {
                "name": "Mug Design",
                "mockup_url": "https://via.placeholder.com/300",
                "quantity": 3,
                "price": 14.99
            }
        ],
        "subtotal": 134.94,
        "shipping_cost": 8.50,
        "total": 143.44
    }

    generator = PackingSlipGenerator()
    pdf_bytes = generator.generate_packing_slip(sample_order)

    # Save to file
    with open("sample_packing_slip.pdf", "wb") as f:
        f.write(pdf_bytes)

    print("Sample packing slip generated: sample_packing_slip.pdf")


if __name__ == "__main__":
    generate_sample_packing_slip()
