import axios from 'axios';
import useAuthStore from '../stores/authStore';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

class PrinterService {
  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api`,
    });

    // Add auth interceptor
    this.api.interceptors.request.use(
      config => {
        const { userToken } = useAuthStore.getState();
        if (userToken) {
          config.headers.Authorization = `Bearer ${userToken}`;
        }
        return config;
      },
      error => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401) {
          useAuthStore.getState().clearUserAuth();
        }
        return Promise.reject(error);
      }
    );
  }

  // Get user's printers
  async getUserPrinters() {
    try {
      const response = await this.api.get('/printers/');
      return {
        success: true,
        data: response.data.printers || response.data, // Handle both new format (with .printers) and legacy format
      };
    } catch (error) {
      console.error('Failed to get user printers:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load printers',
      };
    }
  }

  // Get printer by ID
  async getPrinter(printerId) {
    try {
      const response = await this.api.get(`/printers/${printerId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to get printer:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load printer',
      };
    }
  }

  // Create new printer
  async createPrinter(printerData) {
    try {
      console.log('Creating printer with data:', printerData);
      const response = await this.api.post('/printers/', printerData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to create printer:', error);
      console.error('Error response:', error.response?.data);
      return {
        success: false,
        error: error.response?.data || error.response?.data?.detail || 'Failed to create printer',
      };
    }
  }

  // Update printer
  async updatePrinter(printerId, printerData) {
    try {
      const response = await this.api.put(`/printers/${printerId}`, printerData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to update printer:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update printer',
      };
    }
  }

  // Delete printer
  async deletePrinter(printerId) {
    try {
      await this.api.delete(`/printers/${printerId}`);
      return {
        success: true,
      };
    } catch (error) {
      console.error('Failed to delete printer:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to delete printer',
      };
    }
  }

  // Set default printer
  async setDefaultPrinter(printerId) {
    try {
      const response = await this.api.post(`/printers/${printerId}/set-default`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to set default printer:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to set default printer',
      };
    }
  }

  // Check printer capability for specific requirements
  async checkPrinterCapability(printerId, requirements) {
    try {
      const response = await this.api.post(`/printers/${printerId}/check-capability`, requirements);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to check printer capability:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to check printer capability',
      };
    }
  }

  // Get available templates for printer
  async getPrinterTemplates(printerId) {
    try {
      const response = await this.api.get(`/printers/${printerId}/templates`);
      return {
        success: true,
        data: response.data.templates || response.data,
      };
    } catch (error) {
      console.error('Failed to get printer templates:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load printer templates',
      };
    }
  }

  // Add template to printer
  async addTemplateToPrinter(printerId, templateId) {
    try {
      const response = await this.api.post(`/printers/${printerId}/templates/${templateId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to add template to printer:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to add template to printer',
      };
    }
  }

  // Remove template from printer
  async removeTemplateFromPrinter(printerId, templateId) {
    try {
      const response = await this.api.delete(`/printers/${printerId}/templates/${templateId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to remove template from printer:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to remove template from printer',
      };
    }
  }
}

export default new PrinterService();
