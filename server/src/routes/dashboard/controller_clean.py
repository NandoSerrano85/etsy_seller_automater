# from fastapi import APIRouter, Depends, Query
# from server.src.routes.auth.service import CurrentUser
# from . import model
# from . import service

# router = APIRouter(
#     prefix='/dashboard',
#     tags=['Dashboard']
# )

# @router.get('/analytics', response_model=model.MonthlyAnalyticsResponse)
# async def get_monthly_analytics(
#     current_user: CurrentUser,
#     access_token: str = Query(..., description="Etsy access token"),
#     year: int = Query(None, description="Year for analytics")
# ):
#     """Get analytics data for the current user's Etsy shop"""
#     return service.get_monthly_analytics(access_token, year, current_user)