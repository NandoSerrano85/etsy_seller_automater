import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useOrganizationStore = create(
  persist(
    (set, get) => ({
      // Current organization
      currentOrganization: null,
      organizations: [],
      organizationLoading: false,
      organizationError: null,

      // Organization management actions
      setCurrentOrganization: organization =>
        set({
          currentOrganization: organization,
          organizationError: null,
        }),

      setOrganizations: organizations =>
        set({
          organizations,
          organizationError: null,
        }),

      addOrganization: organization =>
        set(state => ({
          organizations: [...state.organizations, organization],
          organizationError: null,
        })),

      updateOrganization: updatedOrg =>
        set(state => ({
          organizations: state.organizations.map(org => (org.id === updatedOrg.id ? updatedOrg : org)),
          currentOrganization: state.currentOrganization?.id === updatedOrg.id ? updatedOrg : state.currentOrganization,
          organizationError: null,
        })),

      removeOrganization: organizationId =>
        set(state => ({
          organizations: state.organizations.filter(org => org.id !== organizationId),
          currentOrganization: state.currentOrganization?.id === organizationId ? null : state.currentOrganization,
          organizationError: null,
        })),

      setOrganizationLoading: loading => set({ organizationLoading: loading }),

      setOrganizationError: error => set({ organizationError: error }),

      clearOrganizationData: () =>
        set({
          currentOrganization: null,
          organizations: [],
          organizationError: null,
        }),

      // Helper methods
      getUserRole: () => {
        const { currentOrganization } = get();
        return currentOrganization?.user_role || 'member';
      },

      isAdmin: () => {
        const { getUserRole } = get();
        return getUserRole() === 'admin';
      },

      isOwner: () => {
        const { getUserRole } = get();
        return getUserRole() === 'owner';
      },

      hasAdminAccess: () => {
        const { getUserRole } = get();
        const role = getUserRole();
        return role === 'admin' || role === 'owner';
      },

      // Debug info
      getDebugInfo: () => {
        const state = get();
        return {
          currentOrganization: {
            id: state.currentOrganization?.id,
            name: state.currentOrganization?.name,
            userRole: state.currentOrganization?.user_role,
          },
          organizationCount: state.organizations.length,
          hasAdminAccess: state.hasAdminAccess(),
          loading: state.organizationLoading,
          error: state.organizationError,
        };
      },
    }),
    {
      name: 'organization-store',
      partialize: state => ({
        currentOrganization: state.currentOrganization,
        organizations: state.organizations,
      }),
    }
  )
);

export default useOrganizationStore;
