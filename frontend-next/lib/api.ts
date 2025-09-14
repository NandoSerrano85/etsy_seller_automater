import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getUserData() {
  const response = await apiClient.get('/api/user');
  return response.data;
}

export async function getTopSellers() {
  const response = await apiClient.get('/api/top-sellers');
  return response.data;
}

export async function getShopListings() {
  const response = await apiClient.get('/api/shop-listings');
  return response.data;
}

export async function postMasks(payload: any) {
  const response = await apiClient.post('/api/masks', payload);
  return response.data;
}

export async function postMockup(payload: any) {
  const response = await apiClient.post('/api/mockups', payload);
  return response.data;
}