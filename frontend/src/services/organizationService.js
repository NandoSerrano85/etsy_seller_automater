import axios from 'axios';
import useAuthStore from '../stores/authStore';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3003';

class OrganizationService {
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
          // Token expired, clear auth
          useAuthStore.getState().clearUserAuth();
        }
        return Promise.reject(error);
      }
    );
  }

  // Get user's organizations
  async getUserOrganizations() {
    try {
      const response = await this.api.get('/organizations/');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to get user organizations:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load organizations',
      };
    }
  }

  // Get organization details
  async getOrganization(organizationId) {
    try {
      const response = await this.api.get(`/organizations/${organizationId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to get organization:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load organization',
      };
    }
  }

  // Create new organization
  async createOrganization(organizationData) {
    try {
      const response = await this.api.post('/organizations', organizationData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to create organization:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create organization',
      };
    }
  }

  // Update organization
  async updateOrganization(organizationId, organizationData) {
    try {
      const response = await this.api.put(`/organizations/${organizationId}`, organizationData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to update organization:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update organization',
      };
    }
  }

  // Delete organization
  async deleteOrganization(organizationId) {
    try {
      await this.api.delete(`/organizations/${organizationId}`);
      return {
        success: true,
      };
    } catch (error) {
      console.error('Failed to delete organization:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to delete organization',
      };
    }
  }

  // Get organization members
  async getOrganizationMembers(organizationId) {
    try {
      const response = await this.api.get(`/organizations/${organizationId}/members`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to get organization members:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load members',
      };
    }
  }

  // Invite user to organization
  async inviteUser(organizationId, inviteData) {
    try {
      const response = await this.api.post(`/organizations/${organizationId}/invite`, inviteData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to invite user:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to send invitation',
      };
    }
  }

  // Update member role
  async updateMemberRole(organizationId, userId, role) {
    try {
      const response = await this.api.put(`/organizations/${organizationId}/members/${userId}`, {
        role,
      });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Failed to update member role:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update member role',
      };
    }
  }

  // Remove member from organization
  async removeMember(organizationId, userId) {
    try {
      await this.api.delete(`/organizations/${organizationId}/members/${userId}`);
      return {
        success: true,
      };
    } catch (error) {
      console.error('Failed to remove member:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to remove member',
      };
    }
  }
}

export default new OrganizationService();
