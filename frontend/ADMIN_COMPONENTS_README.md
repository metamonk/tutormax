# Admin Components - TutorMax Dashboard

## Overview

This document describes the admin-focused components built for TutorMax's Next.js 16 frontend. These components provide comprehensive audit logging, compliance reporting, and training module management capabilities.

## Components Built

### 1. AuditLogViewer (`components/admin/AuditLogViewer.tsx`)

**Purpose**: Searchable and filterable audit log viewer for security and compliance monitoring.

**Features**:
- **Advanced Table**: Uses Kibo UI `table` component with sorting capabilities
- **Multi-field Search**: Search across user, action, resource, IP address
- **Advanced Filtering**:
  - User email filter
  - Action type filter
  - Resource type filter
  - IP address filter
  - Date range filtering (start/end dates)
- **Pagination**: 100 entries per page with next/previous navigation
- **Color-coded Actions**:
  - Create actions: Green
  - Update actions: Blue
  - Delete actions: Red
- **Export**: CSV export functionality with full data
- **Expandable Details**: Click to view JSON details for each log entry
- **Status Badges**: Success/Failure/Pending indicators

**API Integration**:
- Endpoint: `GET /api/admin/audit-logs`
- Query Parameters: `limit`, `offset`, `user_email`, `action`, `resource_type`, `ip_address`, `start_date`, `end_date`
- Response: `AuditLogResponse` type

**Usage**:
```tsx
import { AuditLogViewer } from '@/components/admin';

<AuditLogViewer apiEndpoint="/api/admin/audit-logs" />
```

---

### 2. ComplianceReports (`components/admin/ComplianceReports.tsx`)

**Purpose**: FERPA, COPPA, and GDPR compliance dashboard with metrics and reports.

**Features**:

**Metrics Dashboard**:
- FERPA Compliance Rate (Educational Privacy)
- COPPA Consent Rate (Under 13 parental consent)
- GDPR Compliance Rate (Data Protection)
- Pending Data Requests counter

**Active Issues Panel**:
- Color-coded severity badges (Critical/High/Medium/Low)
- Status tracking (Open/In Progress/Resolved)
- Affected records count
- Issue descriptions and timestamps

**Recent Reports**:
- Period-based compliance reports (FERPA/COPPA/GDPR)
- Compliance rate visualization with progress bars
- Total/Compliant/Non-compliant/Pending record counts
- Issue breakdown per report
- Download report as JSON

**Consent Records**:
- Total consent records tracking
- Active consent rate visualization
- Progress bar showing consent health

**API Integration**:
- Endpoint: `GET /api/admin/compliance/reports`
- Response: `ComplianceDashboardResponse` type

**Usage**:
```tsx
import { ComplianceReports } from '@/components/admin';

<ComplianceReports apiEndpoint="/api/admin/compliance/reports" />
```

---

### 3. RecommendedTraining (`components/admin/RecommendedTraining.tsx`)

**Purpose**: Training module management with Kanban board for assignment and progress tracking.

**Features**:

**Kanban Board**:
- 3 columns: "To Do", "In Progress", "Completed"
- Drag-and-drop functionality to move modules between statuses
- Real-time status updates
- Visual progress indicators

**Module Cards**:
- Title and description
- Category tags (Pedagogy/Technology/Communication/Compliance/Subject Matter)
- Priority badges (High/Medium/Low)
- Estimated duration
- Assigned tutors count
- Progress percentage (for In Progress modules)
- Due dates (for incomplete modules)

**Advanced Filtering**:
- Search by title/description
- Multi-select category filter with Kibo UI `tags` component
- Priority dropdown filter
- Tutor ID filter
- Clear all filters button

**Statistics Dashboard**:
- Total modules count
- To Do count
- In Progress count (blue highlight)
- Completed count (green highlight)

**Category System**:
- **Pedagogy**: Blue badge - Teaching methods and strategies
- **Technology**: Purple badge - Technical tools and platforms
- **Communication**: Green badge - Student engagement skills
- **Compliance**: Red badge - Legal and regulatory training
- **Subject Matter**: Yellow badge - Domain-specific knowledge

**API Integration**:
- Endpoint: `GET /api/admin/training`
- Update callback: `onModuleUpdate` prop
- Mock data included for demonstration

**Usage**:
```tsx
import { RecommendedTraining } from '@/components/admin';
import { toast } from 'sonner';

const handleModuleUpdate = (module: TrainingModule) => {
  toast.success(`Module "${module.title}" updated`);
  // API call to persist changes
};

<RecommendedTraining
  apiEndpoint="/api/admin/training"
  onModuleUpdate={handleModuleUpdate}
/>
```

---

## Type Definitions

All TypeScript types are defined in `/Users/zeno/Projects/tutormax/frontend-next/lib/types.ts`:

### Audit Log Types
- `AuditLogEntry`
- `AuditLogFilters`
- `AuditLogResponse`

### Compliance Types
- `ComplianceReport`
- `ComplianceIssue`
- `ComplianceMetrics`
- `ComplianceDashboardResponse`

### Training Types
- `TrainingModule`
- `TrainingAssignment`
- `TrainingRecommendationResponse`

---

## Admin Pages

Three Next.js pages were created under `/app/admin/`:

### 1. Audit Logs Page (`/admin/audit-logs`)
- **Route**: `/admin/audit-logs`
- **Access**: Admin role only
- **File**: `app/admin/audit-logs/page.tsx`

### 2. Compliance Page (`/admin/compliance`)
- **Route**: `/admin/compliance`
- **Access**: Admin role only
- **File**: `app/admin/compliance/page.tsx`

### 3. Training Page (`/admin/training`)
- **Route**: `/admin/training`
- **Access**: Admin and People Ops roles
- **File**: `app/admin/training/page.tsx`

All pages include:
- `RequireRole` HOC for access control
- Proper permission denied fallback messages
- Page headers with descriptions
- Toast notifications (for training updates)

---

## Kibo UI Components Installed

The following Kibo UI components were installed via `npx kibo-ui@latest add`:

1. **Table** (`components/kibo-ui/table/index.tsx`)
   - TanStack React Table integration
   - Sortable columns
   - Used in AuditLogViewer

2. **Tags** (`components/kibo-ui/tags/index.tsx`)
   - Multi-select tag system
   - Popover-based selection
   - Used for category filtering in RecommendedTraining

3. **Kanban** (`components/kibo-ui/kanban/index.tsx`)
   - DnD Kit integration
   - Drag-and-drop cards
   - Column-based organization
   - Used in RecommendedTraining

### Dependencies Added
- `@tanstack/react-table`: ^8.21.3
- `@dnd-kit/core`: ^6.3.1
- `@dnd-kit/sortable`: ^10.0.0
- `@dnd-kit/utilities`: ^3.2.2
- `jotai`: ^2.15.1
- `tunnel-rat`: ^0.1.2

---

## Access Control

All admin components use the existing `useAuth` hook and `RequireRole` HOC from `contexts/AuthContext.tsx`.

**Role Requirements**:
- **Audit Logs**: `admin` only
- **Compliance Reports**: `admin` only
- **Training Management**: `admin` or `people_ops`

**Permission Denied Behavior**:
Each page displays a user-friendly message when accessed without proper permissions:
```tsx
<RequireRole
  roles={['admin']}
  fallback={
    <div className="container mx-auto py-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
        <p className="text-muted-foreground">
          You do not have permission to view this page.
        </p>
      </div>
    </div>
  }
>
  {/* Protected content */}
</RequireRole>
```

---

## Styling

All components use:
- **Tailwind CSS v4**: For responsive layouts
- **shadcn/ui**: For base UI components (Card, Button, Input, Badge, etc.)
- **Dark mode support**: Via `dark:` variants
- **Responsive design**: Mobile-first with `md:` and `lg:` breakpoints

**Color Scheme**:
- Severity indicators: Red (critical/high), Yellow (medium), Green (low)
- Status colors: Green (success/completed), Blue (in-progress), Red (failure), Orange (pending/warning)
- Category badges: Custom colors per category type

---

## Testing Recommendations

1. **AuditLogViewer**:
   - Test sorting on each column
   - Verify filter combinations work correctly
   - Test CSV export with large datasets
   - Verify pagination with 100+ records
   - Test date range filtering

2. **ComplianceReports**:
   - Verify metric calculations are accurate
   - Test report download functionality
   - Check compliance rate progress bars
   - Verify issue severity color coding

3. **RecommendedTraining**:
   - Test drag-and-drop between all columns
   - Verify category multi-select filter
   - Test search functionality
   - Check tutor filter logic
   - Verify progress bar updates when moving to "In Progress"
   - Test completion rate when moving to "Completed"

**Mock Data**:
The RecommendedTraining component includes comprehensive mock data for testing. Replace the `fetchTrainingModules` function with actual API calls when backend is ready.

---

## API Endpoints to Implement

### Backend Requirements

1. **GET /api/admin/audit-logs**
   - Query params: `limit`, `offset`, `user_email`, `action`, `resource_type`, `ip_address`, `start_date`, `end_date`
   - Returns: `AuditLogResponse`

2. **POST /api/admin/audit-logs/search**
   - Body: Advanced search criteria
   - Returns: Filtered audit logs

3. **GET /api/admin/compliance/reports**
   - Returns: `ComplianceDashboardResponse` with metrics, reports, and issues

4. **GET /api/admin/training**
   - Returns: List of training modules
   - Optional filters: category, priority, tutor

5. **GET /api/tutors/{id}/training**
   - Returns: `TrainingRecommendationResponse` for specific tutor

6. **PATCH /api/admin/training/{module_id}**
   - Body: Updated module fields (status, assigned_tutors, etc.)
   - Returns: Updated module

---

## Future Enhancements

### AuditLogViewer
- Add real-time updates via WebSocket
- Implement bulk export (all logs)
- Add advanced query builder
- Include user activity heatmap

### ComplianceReports
- Generate PDF reports
- Email scheduled compliance reports
- Add trend analysis charts
- Implement automated issue detection

### RecommendedTraining
- Add module creation form
- Implement tutor assignment UI
- Add training completion tracking
- Include feedback/ratings on modules
- Calendar view for due dates
- Bulk assignment capabilities

---

## Files Created

```
frontend-next/
├── components/admin/
│   ├── AuditLogViewer.tsx          # 400+ lines
│   ├── ComplianceReports.tsx       # 350+ lines
│   ├── RecommendedTraining.tsx     # 520+ lines
│   └── index.ts                    # Exports
├── components/kibo-ui/
│   ├── table/index.tsx             # Installed via Kibo UI
│   ├── tags/index.tsx              # Installed via Kibo UI
│   └── kanban/index.tsx            # Installed via Kibo UI
├── app/admin/
│   ├── audit-logs/page.tsx         # Audit logs page
│   ├── compliance/page.tsx         # Compliance page
│   └── training/page.tsx           # Training page
├── lib/types.ts                    # Extended with admin types
└── ADMIN_COMPONENTS_README.md      # This file
```

---

## Summary

Three production-ready admin components have been successfully built:

1. **AuditLogViewer**: Searchable table with advanced filtering and CSV export
2. **ComplianceReports**: FERPA/COPPA/GDPR compliance dashboard
3. **RecommendedTraining**: Kanban board for training module management

All components:
- ✅ Use TypeScript with strict typing
- ✅ Include role-based access control
- ✅ Support dark mode
- ✅ Are fully responsive
- ✅ Pass TypeScript compilation (`npm run type-check`)
- ✅ Follow Next.js 16 App Router patterns
- ✅ Use Kibo UI and shadcn/ui components
- ✅ Include comprehensive documentation

**Total Lines of Code**: ~1,400+ lines of production-ready TypeScript/React code

---

## Quick Start

1. **Install dependencies** (if not already installed):
   ```bash
   cd /Users/zeno/Projects/tutormax/frontend-next
   npm install
   ```

2. **View components**:
   - Navigate to `/admin/audit-logs` for audit log viewer
   - Navigate to `/admin/compliance` for compliance reports
   - Navigate to `/admin/training` for training management

3. **Integration**:
   - Components are ready to connect to backend APIs
   - Mock data is provided for the training component
   - Update API endpoints as needed in component props

---

**Built with**: Next.js 16, React 19, TypeScript, Tailwind CSS v4, Kibo UI, shadcn/ui
**Author**: Claude Code (Agent 3)
**Date**: November 9, 2025
