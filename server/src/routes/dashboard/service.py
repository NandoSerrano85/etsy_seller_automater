import os
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
from fastapi import HTTPException
from . import model

API_CONFIG = {
    'base_url': 'https://openapi.etsy.com/v3',
}

def get_oauth_variables():
    return {
        'clientID': os.getenv('CLIENT_ID'),
        'clientSecret': os.getenv('CLIENT_SECRET'),
    }

def create_robust_session():
    """Create a requests session with retry logic and timeouts."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        backoff_factor=1,  # Wait time between retries (1, 2, 4 seconds)
        raise_on_status=False  # Don't raise exception on final failure
    )
    
    # Configure adapter with retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def make_robust_request(session, method, url, headers=None, params=None, timeout=30, **kwargs):
    """Make a robust HTTP request with proper error handling."""
    try:
        response = session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            timeout=timeout,
            **kwargs
        )
        
        # Log the request for debugging
        logging.debug(f"{method} {url} - Status: {response.status_code}")
        
        if not response.ok:
            logging.error(f"API request failed: {method} {url} - Status: {response.status_code}, Response: {response.text[:200]}...")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Etsy API error: {response.status_code} - {response.text[:200]}..."
            )
        
        return response.json()
        
    except requests.exceptions.Timeout:
        logging.error(f"Request timeout: {method} {url}")
        raise HTTPException(status_code=504, detail="Request timeout - Etsy API took too long to respond")
    
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error: {method} {url} - {str(e)}")
        raise HTTPException(status_code=503, detail="Connection error - Unable to connect to Etsy API")
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {method} {url} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    
    except Exception as e:
        logging.error(f"Unexpected error: {method} {url} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def get_user_shop_id(access_token: str) -> str:
    """Get the user's shop ID from Etsy API."""
    oauth_vars = get_oauth_variables()
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    
    session = create_robust_session()
    
    try:
        # First get the user's shops
        shops_url = f"{API_CONFIG['base_url']}/application/users/me/shops"
        response_data = make_robust_request(session, 'GET', shops_url, headers=headers)
        
        if 'results' in response_data and len(response_data['results']) > 0:
            shop_id = str(response_data['results'][0]['shop_id'])
            logging.info(f"Retrieved shop ID: {shop_id}")
            return shop_id
        else:
            logging.error("No shops found for user")
            raise HTTPException(status_code=404, detail="No Etsy shops found for this user")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting user shop ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get shop information: {str(e)}")
    finally:
        session.close()

def get_monthly_analytics(access_token: str, year: Optional[int], current_user) -> model.MonthlyAnalyticsResponse:
    """Get monthly analytics for the year."""
    oauth_vars = get_oauth_variables()
    if year is None:
        year = time.localtime().tm_year
    
    logging.info(f"Monthly analytics request - Year: {year}, Access token: {access_token[:8]}...")
    
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    
    # Create robust session with retry logic
    session = create_robust_session()
    
    try:
        # Get shop ID dynamically from Etsy API
        final_shop_id = get_user_shop_id(access_token)
        
        # Fetch receipts with robust pagination
        transactions_url = f"{API_CONFIG['base_url']}/application/shops/{final_shop_id}/receipts"
        start_timestamp = int(time.mktime(time.strptime(f"{year}-01-01", "%Y-%m-%d")))
        end_timestamp = int(time.mktime(time.strptime(f"{year}-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")))
        
        all_receipts = []
        offset = 0
        limit = 100
        max_pages = 50  # Prevent infinite loops - max 5000 receipts
        page_count = 0
        
        logging.info(f"Fetching receipts from {year}-01-01 to {year}-12-31...")
        
        while page_count < max_pages:
            params = {
                'limit': limit,
                'offset': offset,
                'min_created': start_timestamp,
                'max_created': end_timestamp
            }
            
            logging.debug(f"Fetching receipts page {page_count + 1}, offset: {offset}")
            
            transactions_data = make_robust_request(
                session, 'GET', transactions_url, 
                headers=headers, params=params, timeout=30
            )
            
            current_receipts = transactions_data.get('results', [])
            all_receipts.extend(current_receipts)
            
            logging.debug(f"Retrieved {len(current_receipts)} receipts on page {page_count + 1}")
            
            # Break if we got fewer results than limit (last page)
            if len(current_receipts) < limit:
                break
                
            offset += limit
            page_count += 1
        
        logging.info(f"Successfully retrieved {len(all_receipts)} total receipts")
        monthly_data = {month: {
            'total_sales': 0.0,
            'total_quantity': 0,
            'total_discounts': 0.0,
            'net_sales': 0.0,
            'item_sales': {},
            'receipt_count': 0
        } for month in range(1, 13)}
        for receipt in all_receipts:
            receipt_date = time.localtime(receipt.get('created_timestamp', 0))
            month = receipt_date.tm_mon
            if month in monthly_data:
                monthly_data[month]['receipt_count'] += 1
                total_qty = sum(transaction.get('quantity', 1) for transaction in receipt.get('transactions', []))
                discount_val = receipt['subtotal']['amount'] // total_qty if total_qty > 0 else 0
                for transaction in receipt.get('transactions', []):
                    listing_id = transaction.get('listing_id')
                    title = transaction.get('title', 'Unknown Item')
                    quantity = transaction.get('quantity', 1)
                    price = float(transaction.get('price', {}).get('amount', 0))
                    monthly_data[month]['total_sales'] += price * quantity
                    monthly_data[month]['total_quantity'] += quantity
                    monthly_data[month]['total_discounts'] += discount_val * quantity
                    if listing_id not in monthly_data[month]['item_sales']:
                        monthly_data[month]['item_sales'][listing_id] = {
                            'title': title,
                            'quantity_sold': 0,
                            'total_amount': 0.0,
                            'total_discounts': 0.0
                        }
                    monthly_data[month]['item_sales'][listing_id]['quantity_sold'] += quantity
                    monthly_data[month]['item_sales'][listing_id]['total_amount'] += price * quantity
                    monthly_data[month]['item_sales'][listing_id]['total_discounts'] += discount_val * quantity
        monthly_breakdown = []
        total_year_sales = 0.0
        total_year_quantity = 0
        total_year_discounts = 0.0
        total_year_net = 0.0
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        for month in range(1, 13):
            month_data = monthly_data[month]
            month_data['net_sales'] = month_data['total_sales'] - month_data['total_discounts']
            top_items = []
            for listing_id, item_data in month_data['item_sales'].items():
                net_amount = item_data['total_amount'] - item_data['total_discounts']
                top_items.append(model.TopSeller(
                    listing_id=listing_id,
                    title=item_data['title'],
                    quantity_sold=item_data['quantity_sold'],
                    total_amount=item_data['total_amount'],
                    total_discounts=item_data['total_discounts'],
                    net_amount=net_amount
                ))
            top_items.sort(key=lambda x: x.net_amount, reverse=True)
            monthly_breakdown.append(model.MonthlyBreakdown(
                month=month,
                month_name=month_names[month - 1],
                total_sales=month_data['total_sales'],
                total_quantity=month_data['total_quantity'],
                total_discounts=month_data['total_discounts'],
                net_sales=month_data['net_sales'],
                receipt_count=month_data['receipt_count'],
                top_items=top_items[:5]
            ))
            total_year_sales += month_data['total_sales']
            total_year_quantity += month_data['total_quantity']
            total_year_discounts += month_data['total_discounts']
            total_year_net += month_data['net_sales']
        all_item_sales = {}
        for receipt in all_receipts:
            total_qty = sum(transaction.get('quantity', 1) for transaction in receipt.get('transactions', []))
            discount_val = receipt['subtotal']['amount'] // total_qty if total_qty > 0 else 0
            for transaction in receipt.get('transactions', []):
                listing_id = transaction.get('listing_id')
                title = transaction.get('title', 'Unknown Item')
                quantity = transaction.get('quantity', 1)
                price = float(transaction.get('price', {}).get('amount', 0))
                if listing_id not in all_item_sales:
                    all_item_sales[listing_id] = {
                        'title': title,
                        'quantity_sold': 0,
                        'total_amount': 0.0,
                        'total_discounts': 0.0
                    }
                all_item_sales[listing_id]['quantity_sold'] += quantity
                all_item_sales[listing_id]['total_amount'] += price * quantity
                all_item_sales[listing_id]['total_discounts'] += discount_val * quantity
        year_top_sellers = []
        for listing_id, data in all_item_sales.items():
            net_amount = data['total_amount'] - data['total_discounts']
            year_top_sellers.append(model.TopSeller(
                listing_id=listing_id,
                title=data['title'],
                quantity_sold=data['quantity_sold'],
                total_amount=data['total_amount'],
                total_discounts=data['total_discounts'],
                net_amount=net_amount
            ))
        year_top_sellers.sort(key=lambda x: x.net_amount, reverse=True)
        return model.MonthlyAnalyticsResponse(
            year=year,
            summary=model.AnalyticsSummary(
                total_sales=total_year_sales,
                total_quantity=total_year_quantity,
                total_discounts=total_year_discounts,
                net_sales=total_year_net,
                total_receipts=sum(month.receipt_count for month in monthly_breakdown)
            ),
            monthly_breakdown=monthly_breakdown,
            year_top_sellers=year_top_sellers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching monthly analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch monthly analytics: {str(e)}")
    finally:
        # Clean up the session
        try:
            session.close()
        except:
            pass

def get_top_sellers(access_token: str, year: Optional[int], current_user) -> model.TopSellersResponse:
    """Get top sellers for the year."""
    oauth_vars = get_oauth_variables()
    if year is None:
        year = time.localtime().tm_year
        
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    
    # Create robust session
    session = create_robust_session()
    
    try:
        # Get shop ID dynamically from Etsy API
        final_shop_id = get_user_shop_id(access_token)
        transactions_url = f"{API_CONFIG['base_url']}/application/shops/{final_shop_id}/receipts"
        start_timestamp = int(time.mktime(time.strptime(f"{year}-01-01", "%Y-%m-%d")))
        end_timestamp = int(time.mktime(time.strptime(f"{year}-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")))
        
        all_receipts = []
        offset = 0
        limit = 100
        max_pages = 50  # Prevent infinite loops
        page_count = 0
        
        while page_count < max_pages:
            params = {
                'limit': limit,
                'offset': offset,
                'min_created': start_timestamp,
                'max_created': end_timestamp
            }
            
            transactions_data = make_robust_request(
                session, 'GET', transactions_url,
                headers=headers, params=params, timeout=30
            )
            
            current_receipts = transactions_data.get('results', [])
            all_receipts.extend(current_receipts)
            
            if len(current_receipts) < limit:
                break
                
            offset += limit
            page_count += 1
        item_sales = {}
        for receipt in all_receipts:
            total_qty = sum(transaction.get('quantity', 1) for transaction in receipt.get('transactions', []))
            discount_val = receipt['subtotal']['amount'] // total_qty if total_qty > 0 else 0
            for transaction in receipt.get('transactions', []):
                listing_id = transaction.get('listing_id')
                title = transaction.get('title', 'Unknown Item')
                quantity = transaction.get('quantity', 1)
                price = float(transaction.get('price', {}).get('amount', 0))
                if listing_id not in item_sales:
                    item_sales[listing_id] = {
                        'title': title,
                        'quantity_sold': 0,
                        'total_amount': 0.0,
                        'total_discounts': 0.0
                    }
                item_sales[listing_id]['quantity_sold'] += quantity
                item_sales[listing_id]['total_amount'] += price * quantity
                item_sales[listing_id]['total_discounts'] += discount_val * quantity
        top_sellers = []
        for listing_id, data in item_sales.items():
            net_amount = data['total_amount'] - data['total_discounts']
            top_sellers.append(model.TopSeller(
                listing_id=listing_id,
                title=data['title'],
                quantity_sold=data['quantity_sold'],
                total_amount=data['total_amount'],
                total_discounts=data['total_discounts'],
                net_amount=net_amount
            ))
        top_sellers.sort(key=lambda x: x.net_amount, reverse=True)
        return model.TopSellersResponse(
            year=year,
            top_sellers=top_sellers,
            total_items=len(top_sellers)
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching top sellers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch top sellers: {str(e)}")
    finally:
        # Clean up the session
        try:
            session.close()
        except:
            pass

def get_shop_listings(access_token: str, limit: int, offset: int, current_user) -> model.ShopListingsResponse:
    """Get shop listings/designs."""
    oauth_vars = get_oauth_variables()
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    
    # Create robust session
    session = create_robust_session()
    
    try:
        # Get shop ID dynamically from Etsy API
        final_shop_id = get_user_shop_id(access_token)
        
        listings_url = f"{API_CONFIG['base_url']}/application/shops/{final_shop_id}/listings/active"
        params = {
            'limit': limit,
            'offset': offset,
            'includes': 'Images'
        }
        
        listings_data = make_robust_request(
            session, 'GET', listings_url,
            headers=headers, params=params, timeout=20
        )
        # Local images logic placeholder (customize as needed)
        local_images = []
        designs = []
        for listing in listings_data.get('results', []):
            images = [model.ShopListingImage(
                url_full=image.get('url_fullxfull'),
                url_75=image.get('url_75x75'),
                url_170=image.get('url_170x135'),
                url_570=image.get('url_570xN'),
                url_640=image.get('url_640x640')
            ) for image in listing.get('Images', [])]
            design = model.ShopListing(
                listing_id=listing.get('listing_id'),
                title=listing.get('title'),
                description=listing.get('description'),
                price=listing.get('price', {}).get('amount'),
                currency=listing.get('price', {}).get('divisor'),
                quantity=listing.get('quantity'),
                state=listing.get('state'),
                images=images,
                local_images=local_images
            )
            designs.append(design)
        return model.ShopListingsResponse(
            designs=designs,
            count=len(designs),
            total=listings_data.get('count', 0),
            pagination={
                'limit': limit,
                'offset': offset
            },
            local_images_count=len(local_images)
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching shop listings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch shop listings: {str(e)}")
    finally:
        # Clean up the session
        try:
            session.close()
        except:
            pass