from typing import Dict, Any
from uuid import UUID
import logging
from server.src.utils.etsy_api_engine import EtsyAPI
from server.src.message import (
    ThirdPartyListingError,
    ThirdPartyListingNotFoundError,
    ThirdPartyListingUpdateError
)
from . import model


def _parse_etsy_listing(listing_data: Dict[str, Any]) -> model.ListingResponse:
    """
    Parse Etsy listing data into our ListingResponse model
    """
    # Parse images
    images = []
    default_image_url = None
    
    if 'images' in listing_data and listing_data['images']:
        for img_data in listing_data['images']:
            image = model.ListingImage(
                listing_image_id=img_data.get('listing_image_id'),
                hex_code=img_data.get('hex_code'),
                red=img_data.get('red'),
                green=img_data.get('green'),
                blue=img_data.get('blue'),
                hue=img_data.get('hue'),
                saturation=img_data.get('saturation'),
                brightness=img_data.get('brightness'),
                is_black_and_white=img_data.get('is_black_and_white'),
                creation_tsz=img_data.get('creation_tsz'),
                created_timestamp=img_data.get('created_timestamp'),
                rank=img_data.get('rank'),
                url_75x75=img_data.get('url_75x75'),
                url_170x135=img_data.get('url_170x135'),
                url_570xN=img_data.get('url_570xN'),
                url_fullxfull=img_data.get('url_fullxfull'),
                full_height=img_data.get('full_height'),
                full_width=img_data.get('full_width'),
                alt_text=img_data.get('alt_text')
            )
            images.append(image)
        
        # Set default image URL - use the first image's best quality URL
        if images:
            first_image = listing_data['images'][0]
            # Priority: fullxfull > 570xN > 170x135 > 75x75
            default_image_url = (
                first_image.get('url_fullxfull') or 
                first_image.get('url_570xN') or 
                first_image.get('url_170x135') or 
                first_image.get('url_75x75')
            )
    
    return model.ListingResponse(
        listing_id=listing_data.get('listing_id'),
        title=listing_data.get('title'),
        description=listing_data.get('description'),
        price=listing_data.get('price', {}).get('amount') if listing_data.get('price') else None,
        quantity=listing_data.get('quantity'),
        state=listing_data.get('state'),
        tags=listing_data.get('tags', []),
        materials=listing_data.get('materials', []),
        taxonomy_id=listing_data.get('taxonomy_id'),
        shop_section_id=listing_data.get('shop_section_id'),
        shipping_profile_id=listing_data.get('shipping_profile_id'),
        item_weight=listing_data.get('item_weight'),
        item_weight_unit=listing_data.get('item_weight_unit'),
        item_length=listing_data.get('item_length'),
        item_width=listing_data.get('item_width'),
        item_height=listing_data.get('item_height'),
        item_dimensions_unit=listing_data.get('item_dimensions_unit'),
        return_policy_id=listing_data.get('return_policy_id'),
        who_made=listing_data.get('who_made'),
        when_made=listing_data.get('when_made'),
        is_taxable=listing_data.get('is_taxable'),
        processing_min=listing_data.get('processing_min'),
        processing_max=listing_data.get('processing_max'),
        created_at=listing_data.get('created_timestamp'),
        updated_at=listing_data.get('last_modified_timestamp'),
        images=images,
        default_image_url=default_image_url
    )


def _prepare_update_data(update_request: model.ListingUpdateRequest) -> Dict[str, Any]:
    """
    Convert ListingUpdateRequest to Etsy API format, excluding None values
    """
    update_data = update_request.model_dump(exclude_unset=True)
    
    # Handle price formatting for Etsy API (if price is provided)
    if 'price' in update_data and update_data['price'] is not None:
        # Etsy expects price as a string with currency info, but we'll keep it simple
        pass  # The API engine should handle this
    
    return update_data


def get_shop_listings(user_id: UUID, db, request: model.GetListingsRequest) -> model.ListingsResponse:
    """
    Get shop listings with pagination and filtering
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        response = etsy_api.get_shop_listings(
            state=request.state,
            limit=request.limit or 100,
            offset=request.offset or 0
        )
        
        listings = [_parse_etsy_listing(listing) for listing in response.get('results', [])]
        
        return model.ListingsResponse(
            listings=listings,
            count=len(listings),
            total=response.get('count', 0),
            success_code=200,
            message=f"Retrieved {len(listings)} listings"
        )
        
    except Exception as e:
        logging.error(f"Error getting shop listings for user {user_id}: {e}")
        raise ThirdPartyListingError(f"Failed to get shop listings: {str(e)}")


def get_all_shop_listings(user_id: UUID, db, request: model.GetAllListingsRequest) -> model.ListingsResponse:
    """
    Get all shop listings (with automatic pagination)
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        response = etsy_api.get_all_shop_listings(state=request.state)
        
        listings = [_parse_etsy_listing(listing) for listing in response.get('results', [])]
        
        return model.ListingsResponse(
            listings=listings,
            count=len(listings),
            total=response.get('count', 0),
            success_code=200,
            message=f"Retrieved all {len(listings)} listings"
        )
        
    except Exception as e:
        logging.error(f"Error getting all shop listings for user {user_id}: {e}")
        raise ThirdPartyListingError(f"Failed to get all shop listings: {str(e)}")


def get_listing_by_id(user_id: UUID, db, listing_id: int) -> model.ListingResponse:
    """
    Get a specific listing by ID
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        listing_data = etsy_api.get_listing_by_id(listing_id)
        
        return _parse_etsy_listing(listing_data)
        
    except Exception as e:
        logging.error(f"Error getting listing {listing_id} for user {user_id}: {e}")
        if "404" in str(e):
            raise ThirdPartyListingNotFoundError(listing_id)
        raise ThirdPartyListingError(f"Failed to get listing: {str(e)}")


def update_listing(user_id: UUID, db, listing_id: int, update_request: model.ListingUpdateRequest) -> model.ListingResponse:
    """
    Update a specific listing
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        update_data = _prepare_update_data(update_request)
        
        if not update_data:
            raise ThirdPartyListingUpdateError(listing_id, "No update data provided")
        
        updated_listing = etsy_api.update_listing(listing_id, update_data)
        
        return _parse_etsy_listing(updated_listing)
        
    except Exception as e:
        logging.error(f"Error updating listing {listing_id} for user {user_id}: {e}")
        if "404" in str(e):
            raise ThirdPartyListingNotFoundError(listing_id)
        raise ThirdPartyListingUpdateError(listing_id, str(e))


def bulk_update_listings(user_id: UUID, db, request: model.BulkListingUpdateRequest) -> model.BulkUpdateResponse:
    """
    Update multiple listings with the same data
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        update_data = _prepare_update_data(request.updates)
        
        if not update_data:
            raise ThirdPartyListingError("No update data provided")
        
        # Prepare the updates list for bulk update
        listing_updates = []
        for listing_id in request.listing_ids:
            update_with_id = update_data.copy()
            update_with_id['listing_id'] = listing_id
            listing_updates.append(update_with_id)
        
        results = etsy_api.bulk_update_listings(listing_updates)
        
        # Transform results to our response format
        successful = [
            model.ListingUpdateResult(
                listing_id=result['listing_id'],
                success=True,
                data=_parse_etsy_listing(result['data'])
            )
            for result in results['successful']
        ]
        
        failed = [
            model.ListingUpdateResult(
                listing_id=result['listing_id'],
                success=False,
                error=result['error']
            )
            for result in results['failed']
        ]
        
        return model.BulkUpdateResponse(
            successful=successful,
            failed=failed,
            total=results['total'],
            success_count=len(successful),
            failure_count=len(failed),
            success_code=200,
            message=f"Bulk update completed: {len(successful)} successful, {len(failed)} failed"
        )
        
    except Exception as e:
        logging.error(f"Error bulk updating listings for user {user_id}: {e}")
        raise ThirdPartyListingError(f"Failed to bulk update listings: {str(e)}")


def update_selected_listings(user_id: UUID, db, request: model.SelectedListingsUpdateRequest) -> model.BulkUpdateResponse:
    """
    Update specific listings with individual update data
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        if not request.listing_updates:
            raise ThirdPartyListingError("No listing updates provided")
        
        # Validate that each update has a listing_id
        for update in request.listing_updates:
            if 'listing_id' not in update:
                raise ThirdPartyListingError("Each listing update must contain 'listing_id'")
        
        results = etsy_api.bulk_update_listings(request.listing_updates)
        
        # Transform results to our response format
        successful = [
            model.ListingUpdateResult(
                listing_id=result['listing_id'],
                success=True,
                data=_parse_etsy_listing(result['data'])
            )
            for result in results['successful']
        ]
        
        failed = [
            model.ListingUpdateResult(
                listing_id=result['listing_id'],
                success=False,
                error=result['error']
            )
            for result in results['failed']
        ]
        
        return model.BulkUpdateResponse(
            successful=successful,
            failed=failed,
            total=results['total'],
            success_count=len(successful),
            failure_count=len(failed),
            success_code=200,
            message=f"Selected listings update completed: {len(successful)} successful, {len(failed)} failed"
        )
        
    except Exception as e:
        logging.error(f"Error updating selected listings for user {user_id}: {e}")
        raise ThirdPartyListingError(f"Failed to update selected listings: {str(e)}")


def get_taxonomies(user_id: UUID, db) -> model.TaxonomiesResponse:
    """
    Get all available taxonomies (categories) for listings
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        taxonomies_data = etsy_api.fetch_all_taxonomies()
        
        if not taxonomies_data:
            return model.TaxonomiesResponse(
                taxonomies=[],
                success_code=200,
                message="No taxonomies found"
            )
        
        taxonomies = [
            model.DropdownOption(id=tax["id"], name=tax["name"]) 
            for tax in taxonomies_data
        ]
        
        return model.TaxonomiesResponse(
            taxonomies=taxonomies,
            success_code=200,
            message=f"Retrieved {len(taxonomies)} taxonomies"
        )
        
    except Exception as e:
        logging.error(f"Error getting taxonomies for user {user_id}: {e}")
        raise ThirdPartyListingError(f"Failed to get taxonomies: {str(e)}")


def get_shipping_profiles(user_id: UUID, db) -> model.ShippingProfilesResponse:
    """
    Get all available shipping profiles
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        profiles_data = etsy_api.fetch_all_shipping_profiles()
        
        if not profiles_data:
            return model.ShippingProfilesResponse(
                shipping_profiles=[],
                success_code=200,
                message="No shipping profiles found"
            )
        
        profiles = [
            model.DropdownOption(id=profile["id"], name=profile["name"]) 
            for profile in profiles_data
        ]
        
        return model.ShippingProfilesResponse(
            shipping_profiles=profiles,
            success_code=200,
            message=f"Retrieved {len(profiles)} shipping profiles"
        )
        
    except Exception as e:
        logging.error(f"Error getting shipping profiles for user {user_id}: {e}")
        raise ThirdPartyListingError(f"Failed to get shipping profiles: {str(e)}")


def get_shop_sections(user_id: UUID, db) -> model.ShopSectionsResponse:
    """
    Get all available shop sections
    """
    try:
        etsy_api = EtsyAPI(user_id, db)
        
        sections_data = etsy_api.fetch_all_shop_sections()
        
        if not sections_data:
            return model.ShopSectionsResponse(
                shop_sections=[],
                success_code=200,
                message="No shop sections found"
            )
        
        sections = [
            model.DropdownOption(id=section["id"], name=section["name"]) 
            for section in sections_data
        ]
        
        return model.ShopSectionsResponse(
            shop_sections=sections,
            success_code=200,
            message=f"Retrieved {len(sections)} shop sections"
        )
        
    except Exception as e:
        logging.error(f"Error getting shop sections for user {user_id}: {e}")
        raise ThirdPartyListingError(f"Failed to get shop sections: {str(e)}")