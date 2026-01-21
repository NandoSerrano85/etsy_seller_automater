# CraftFlow Email Management Pages - Implementation Guide

## Location

All pages should be created in: `/frontend/src/pages/CraftFlow/Emails/`

## Pages to Create (6 total)

### 1. EmailTemplates.js - Template List & Management

**Route**: `/craftflow/emails/templates`
**Features**:

- List all email templates with cards
- Filters: email_type, is_active
- Actions: Create, Edit, Delete, Preview
- Uses axios with Bearer token from `useAuth()`

### 2. EmailTemplateEditor.js - Create/Edit Template

**Route**: `/craftflow/emails/templates/new` or `/craftflow/emails/templates/edit/:id`
**Features**:

- Form with metadata (name, type, subject)
- Branding (colors, logo)
- Block editor with 8 block types
- Move blocks up/down, delete
- Save/Cancel actions

### 3. EmailLogs.js - Email Log Viewer

**Route**: `/craftflow/emails/logs`
**Features**:

- Table with pagination
- Filters: email_type, status, date range
- Status badges (sent, delivered, opened, clicked, bounced, failed)
- View details action

### 4. EmailAnalytics.js - Analytics Dashboard

**Route**: `/craftflow/emails/analytics`
**Features**:

- Summary cards (total sent, delivery rate, open rate, click rate)
- Date range filter (7/30/90 days, custom)
- Breakdown by email type
- Performance table

### 5. EmailSubscribers.js - Subscriber Management

**Route**: `/craftflow/emails/subscribers`
**Features**:

- Table with search and filters
- Add/Edit/Delete subscriber
- Tags management
- CSV import/export

### 6. EmailCampaigns.js - Campaign Management

**Route**: `/craftflow/emails/campaigns`
**Features**:

- List scheduled campaigns with status
- Create campaign form (multi-step)
- Cancel pending campaigns
- View campaign details

## API Integration Pattern

```javascript
import axios from "axios";
import { useAuth } from "../../../hooks/useAuth";
import { useNotifications } from "../../../components/NotificationSystem";

const { userToken: token } = useAuth();
const { addNotification } = useNotifications();
const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:3003";

// Example API call
const response = await axios.get(
  `${API_BASE_URL}/api/ecommerce/admin/emails/templates`,
  {
    headers: { Authorization: `Bearer ${token}` },
  },
);
```

## Icons to Use

Import from `@heroicons/react/24/outline`:

- EnvelopeIcon - Email/Mail
- DocumentTextIcon - Templates
- ChartBarIcon - Analytics
- UserGroupIcon - Subscribers
- CalendarIcon - Campaigns
- FunnelIcon - Filters
- MagnifyingGlassIcon - Search
- PlusIcon - Add/Create
- PencilIcon - Edit
- TrashIcon - Delete

## Routing Updates in App.js

Add these routes after the existing CraftFlow routes (after line 373):

```javascript
// Email Management Routes
const CraftFlowEmailTemplates = React.lazy(() => import('./pages/CraftFlow/Emails/EmailTemplates'));
const CraftFlowEmailTemplateEditor = React.lazy(() => import('./pages/CraftFlow/Emails/EmailTemplateEditor'));
const CraftFlowEmailLogs = React.lazy(() => import('./pages/CraftFlow/Emails/EmailLogs'));
const CraftFlowEmailAnalytics = React.lazy(() => import('./pages/CraftFlow/Emails/EmailAnalytics'));
const CraftFlowEmailSubscribers = React.lazy(() => import('./pages/CraftFlow/Emails/EmailSubscribers'));
const CraftFlowEmailCampaigns = React.lazy(() => import('./pages/CraftFlow/Emails/EmailCampaigns'));

// In Routes section:
<Route path="/craftflow/emails/templates" element={<ProtectedRoute><CraftFlowEmailTemplates /></ProtectedRoute>} />
<Route path="/craftflow/emails/templates/new" element={<ProtectedRoute><CraftFlowEmailTemplateEditor /></ProtectedRoute>} />
<Route path="/craftflow/emails/templates/edit/:id" element={<ProtectedRoute><CraftFlowEmailTemplateEditor /></ProtectedRoute>} />
<Route path="/craftflow/emails/logs" element={<ProtectedRoute><CraftFlowEmailLogs /></ProtectedRoute>} />
<Route path="/craftflow/emails/analytics" element={<ProtectedRoute><CraftFlowEmailAnalytics /></ProtectedRoute>} />
<Route path="/craftflow/emails/subscribers" element={<ProtectedRoute><CraftFlowEmailSubscribers /></ProtectedRoute>} />
<Route path="/craftflow/emails/campaigns" element={<ProtectedRoute><CraftFlowEmailCampaigns /></ProtectedRoute>} />
```

## Navigation Integration

Add email link to CraftFlow section in `SidebarNavigation.js`:

```javascript
{
  name: 'Email Management',
  icon: EnvelopeIcon,
  path: '/craftflow/emails/templates',
  badge: null
}
```

## Component Structure Template

```javascript
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../../hooks/useAuth";
import { useNotifications } from "../../../components/NotificationSystem";
import axios from "axios";
import {} from /* Icons */ "@heroicons/react/24/outline";

const ComponentName = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const API_BASE_URL =
    process.env.REACT_APP_API_BASE_URL || "http://localhost:3003";

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/endpoint`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      // Handle data
    } catch (error) {
      console.error("Error:", error);
      addNotification("error", "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return <div className="space-y-6">{/* Component content */}</div>;
};

export default ComponentName;
```

## Styling

Use Tailwind CSS classes matching the existing CraftFlow pages:

- Containers: `space-y-6`, `max-w-7xl`
- Cards: `bg-white rounded-lg shadow-sm p-6`
- Buttons: `bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700`
- Inputs: `border border-gray-300 rounded-lg px-3 py-2`
- Tables: `min-w-full divide-y divide-gray-200`

## Status Badge Colors

```javascript
const getStatusColor = (status) => {
  const colors = {
    sent: "bg-blue-100 text-blue-800",
    delivered: "bg-green-100 text-green-800",
    opened: "bg-purple-100 text-purple-800",
    clicked: "bg-indigo-100 text-indigo-800",
    bounced: "bg-red-100 text-red-800",
    failed: "bg-red-100 text-red-800",
    pending: "bg-yellow-100 text-yellow-800",
    processing: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
    cancelled: "bg-gray-100 text-gray-800",
  };
  return colors[status] || "bg-gray-100 text-gray-800";
};
```

## Next Steps

1. Create all 6 page components in `/frontend/src/pages/CraftFlow/Emails/`
2. Update `App.js` with lazy-loaded imports and routes
3. Update `SidebarNavigation.js` to add email management link
4. Test each page with the backend API
5. Add proper error handling and loading states
6. Verify all CRUD operations work correctly

---

**Status**: Ready for implementation
**Estimated Time**: 4-6 hours for all pages
**Priority**: High - Part of production readiness requirements
