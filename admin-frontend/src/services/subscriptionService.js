/**
 * Subscription Service
 * Handles API calls for subscription management
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

class SubscriptionService {
  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/subscriptions`,
      withCredentials: true,
    });
  }

  /**
   * Create a Stripe checkout session
   */
  async createCheckoutSession(priceId, successUrl, cancelUrl) {
    try {
      const response = await this.api.post('/checkout', {
        price_id: priceId,
        success_url: successUrl,
        cancel_url: cancelUrl,
      });
      return response.data;
    } catch (error) {
      console.error('Error creating checkout session:', error);
      throw error;
    }
  }

  /**
   * Get current subscription
   */
  async getCurrentSubscription() {
    try {
      const response = await this.api.get('/current');
      return response.data;
    } catch (error) {
      console.error('Error getting current subscription:', error);
      throw error;
    }
  }

  /**
   * Update subscription to a new tier
   */
  async updateSubscription(newPriceId) {
    try {
      const response = await this.api.put('/update', {
        new_price_id: newPriceId,
      });
      return response.data;
    } catch (error) {
      console.error('Error updating subscription:', error);
      throw error;
    }
  }

  /**
   * Cancel subscription
   */
  async cancelSubscription(cancelImmediately = false) {
    try {
      const response = await this.api.post('/cancel', {
        cancel_immediately: cancelImmediately,
      });
      return response.data;
    } catch (error) {
      console.error('Error canceling subscription:', error);
      throw error;
    }
  }

  /**
   * Get billing history
   */
  async getBillingHistory(limit = 10) {
    try {
      const response = await this.api.get('/billing-history', {
        params: { limit },
      });
      return response.data;
    } catch (error) {
      console.error('Error getting billing history:', error);
      throw error;
    }
  }

  /**
   * Create customer portal session
   */
  async createCustomerPortal(returnUrl) {
    try {
      const response = await this.api.post('/customer-portal', null, {
        params: { return_url: returnUrl },
      });
      return response.data;
    } catch (error) {
      console.error('Error creating customer portal:', error);
      throw error;
    }
  }

  /**
   * Get subscription tiers
   */
  async getSubscriptionTiers() {
    try {
      const response = await this.api.get('/tiers');
      return response.data;
    } catch (error) {
      console.error('Error getting subscription tiers:', error);
      throw error;
    }
  }
}

export default new SubscriptionService();
