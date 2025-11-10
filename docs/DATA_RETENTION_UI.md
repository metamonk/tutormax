# Data Retention Management UI - Frontend Documentation

## Overview

The Data Retention Management UI provides administrators with a comprehensive interface to manage data lifecycle, FERPA retention, GDPR deletion requests, and compliance reporting.

## Features

### 1. **Dashboard Overview**
- Real-time metrics cards showing retention status
- Quick action buttons for common tasks
- Visual indicators for compliance status
- Recent activity summary

### 2. **Scan & Archive Tab**
- Scan for records eligible for archival (7+ years old)
- View detailed list of eligible students, tutors, and sessions
- Summary statistics by record type
- Preview of eligible records with activity dates

### 3. **GDPR Deletion Tab**
- Process user deletion requests (Right to be Forgotten)
- Permanent data removal workflow
- Safety warnings and confirmations
- Maintains anonymized audit logs for compliance

### 4. **Reports Tab**
- Current data inventory (active students, tutors, sessions)
- Retention actions taken (archival, anonymization, deletions)
- Compliance status summary
- Date range selection for historical reports

### 5. **Policy Tab**
- FERPA retention policy details
- GDPR compliance settings
- Automated archival configuration
- Data lifecycle stages

## Component Structure

```
frontend/
├── app/admin/data-retention/
│   └── page.tsx                    # Admin page with RBAC protection
├── components/admin/
│   ├── DataRetentionDashboard.tsx  # Main dashboard component
│   └── index.ts                    # Component exports
└── lib/
    ├── api.ts                      # API client with retention methods
    └── types.ts                    # TypeScript type definitions
```

## Usage

### Accessing the UI

1. **Login as Administrator**
   - Only users with `admin` role can access
   - Navigate to `/admin/data-retention`

2. **Dashboard Loads Automatically**
   - Retention policy loads on mount
   - Overview cards display current status

### Running a Retention Scan

```typescript
// Dry run (safe, no changes made)
const handleScan = async () => {
  const results = await apiClient.scanRetention(true);
  // Results show eligible records for archival
};
```

**UI Flow:**
1. Click "Run Scan" button
2. Loading indicator displays
3. Results populate in "Scan & Archive" tab
4. View eligible students, sessions, audit logs
5. Summary cards update with counts

### Generating Reports

```typescript
// Generate 90-day compliance report (default)
const handleReport = async () => {
  const report = await apiClient.getRetentionReport();
  // Report shows all retention actions taken
};
```

**Report Includes:**
- Current data inventory
- Archival operations count
- Anonymization operations count
- Deletion requests processed
- Compliance status for FERPA, GDPR, COPPA

### Processing GDPR Deletion

⚠️ **WARNING: Permanent Operation**

```typescript
// Delete user data permanently
const handleDeletion = async (userId: number) => {
  const result = await apiClient.deleteUserData({
    user_id: userId,
    deletion_reason: "GDPR Article 17 - Right to Erasure"
  });
  // All user data removed, audit logs anonymized
};
```

**What Gets Deleted:**
- User account
- All tutor/student records
- Sessions, feedback, performance metrics
- Interventions, predictions, events
- Manager notes, notifications

**What's Retained:**
- Anonymized audit logs (compliance requirement)

## API Client Methods

### Available Methods

```typescript
// Scan for eligible records
await apiClient.scanRetention(dryRun: boolean): Promise<RetentionScanResult>

// Archive specific entity
await apiClient.archiveEntity(request: ArchivalRequest): Promise<ArchivalResult>

// Anonymize data for analytics
await apiClient.anonymizeEntity(request: AnonymizationRequest): Promise<AnonymizationResult>

// GDPR deletion
await apiClient.deleteUserData(request: DeletionRequest): Promise<DeletionResult>

// Generate report
await apiClient.getRetentionReport(startDate?: string, endDate?: string): Promise<RetentionReport>

// Get policy details
await apiClient.getRetentionPolicy(): Promise<RetentionPolicy>

// Check specific entity status
await apiClient.checkRetentionStatus(entityType: string, entityId: string): Promise<RetentionStatusCheck>

// Run scheduled archival
await apiClient.runScheduledArchival(performActions: boolean): Promise<any>
```

### Example Usage

```typescript
import { apiClient } from '@/lib/api';

// Component example
export function DataRetentionComponent() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const handleScan = async () => {
    try {
      setLoading(true);
      const scanResults = await apiClient.scanRetention(true);
      setResults(scanResults);
      toast.success('Scan completed');
    } catch (error) {
      toast.error('Scan failed');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button onClick={handleScan} disabled={loading}>
      {loading ? 'Scanning...' : 'Run Scan'}
    </Button>
  );
}
```

## Type Definitions

All TypeScript interfaces are defined in `frontend/lib/types.ts`:

### Key Types

```typescript
// Scan results
interface RetentionScanResult {
  scan_date: string;
  eligible_for_archival: {
    students: EligibleStudent[];
    tutors: EligibleTutor[];
    sessions: EligibleSession[];
    // ...
  };
  summary: RetentionSummary;
}

// Archival request/result
interface ArchivalRequest {
  entity_type: 'student' | 'tutor';
  entity_id: string;
  reason?: string;
}

interface ArchivalResult {
  archive_id: string;
  entity_id: string;
  archive_date: string;
  archived_records: {...};
}

// Deletion request/result
interface DeletionRequest {
  user_id: number;
  deletion_reason?: string;
}

interface DeletionResult {
  user_id: number;
  deletion_date: string;
  records_deleted: Record<string, number>;
  records_anonymized: Record<string, number>;
}

// Compliance report
interface RetentionReport {
  report_generated_at: string;
  report_period: {...};
  current_data_inventory: {...};
  retention_actions_taken: {...};
  compliance_status: {...};
}
```

## UI Components

### DataRetentionDashboard

**Location:** `frontend/components/admin/DataRetentionDashboard.tsx`

**Props:** None (manages own state)

**Features:**
- Overview cards with real-time metrics
- Tabbed interface (Scan, GDPR, Reports, Policy)
- Loading states and error handling
- Toast notifications for user feedback
- Responsive design

**State Management:**
```typescript
const [loading, setLoading] = useState(false);
const [policy, setPolicy] = useState<RetentionPolicy | null>(null);
const [scanResults, setScanResults] = useState<RetentionScanResult | null>(null);
const [report, setReport] = useState<RetentionReport | null>(null);
const [error, setError] = useState<string | null>(null);
```

**Lifecycle:**
1. Mount → Load retention policy
2. User action → Update state
3. API call → Show loading
4. Success → Update UI, show toast
5. Error → Display error, show toast

### Page Component

**Location:** `frontend/app/admin/data-retention/page.tsx`

**Features:**
- RBAC protection (admin-only)
- Page layout and header
- Access denied fallback
- Responsive container

**Usage:**
```tsx
<RequireRole
  roles={['admin']}
  fallback={<AccessDenied />}
>
  <DataRetentionDashboard />
</RequireRole>
```

## Styling

Uses Tailwind CSS and shadcn/ui components:

- **Colors:** Semantic color scheme with muted backgrounds
- **Spacing:** Consistent padding and margins
- **Typography:** Clear hierarchy with size/weight variations
- **Components:** Card, Button, Badge, Alert, Tabs from shadcn/ui
- **Icons:** Lucide React icons
- **Responsive:** Mobile-first design with breakpoints

## Error Handling

### API Errors

```typescript
try {
  const results = await apiClient.scanRetention(true);
  // Success
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
    } else if (error.response?.status === 403) {
      // Forbidden - show access denied
    } else {
      // Other error - show error message
      toast.error('Operation failed');
    }
  }
}
```

### UI Error States

- Error alert displayed prominently
- Toast notifications for quick feedback
- Loading states prevent double-clicks
- Graceful degradation on failure

## Security

### RBAC Enforcement

```tsx
<RequireRole roles={['admin']}>
  {/* Admin-only content */}
</RequireRole>
```

**Access Control:**
- Frontend: React component guards
- Backend: API endpoint middleware
- Token: JWT validation on every request

### Dangerous Operations

**Deletion Warnings:**
- Alert component with warning icon
- Descriptive text about permanence
- Confirmation dialogs (when implemented)

**Best Practices:**
- Always use dry run first
- Review scan results before action
- Verify entity IDs before deletion
- Document deletion reasons

## Testing

### Manual Testing Checklist

- [ ] Load dashboard as admin user
- [ ] Verify overview cards display
- [ ] Run retention scan
- [ ] View scan results
- [ ] Generate compliance report
- [ ] Check policy details
- [ ] Test error states (network failure)
- [ ] Verify loading indicators
- [ ] Test responsive design (mobile)
- [ ] Confirm toast notifications work

### Integration Testing

```typescript
// Example test
describe('DataRetentionDashboard', () => {
  it('loads retention policy on mount', async () => {
    render(<DataRetentionDashboard />);
    await waitFor(() => {
      expect(screen.getByText('7 Years')).toBeInTheDocument();
    });
  });

  it('handles scan operation', async () => {
    render(<DataRetentionDashboard />);
    const scanButton = screen.getByText('Run Scan');
    fireEvent.click(scanButton);
    await waitFor(() => {
      expect(screen.getByText(/Scan completed/i)).toBeInTheDocument();
    });
  });
});
```

## Future Enhancements

### Planned Features

1. **Advanced Archival Management**
   - Individual entity archival UI
   - Bulk archival operations
   - Archive restore functionality
   - Archive search and filter

2. **Enhanced GDPR Deletion**
   - User search/autocomplete
   - Deletion request queue
   - Approval workflow
   - Deletion history viewer

3. **Advanced Reporting**
   - Custom date ranges
   - Chart visualizations (Chart.js)
   - Export to PDF/CSV
   - Scheduled report generation

4. **Anonymization Management**
   - Manual anonymization triggers
   - Anonymization preview
   - Bulk anonymization
   - Anonymization audit trail

5. **Real-time Updates**
   - WebSocket integration
   - Live scan progress
   - Automatic dashboard refresh
   - Background job status

### Component Stubs

Additional components can be created:

```
components/admin/
├── RetentionScan.tsx           # Detailed scan interface
├── ArchivalManagement.tsx      # Archival operations
├── GDPRDeletionManagement.tsx  # Deletion workflow
├── DataRetentionReporting.tsx  # Advanced reporting
└── RetentionScheduler.tsx      # Schedule automation
```

## Troubleshooting

### Common Issues

**1. "Failed to load retention policy"**
- Check API connection
- Verify authentication token
- Ensure backend service is running
- Check CORS configuration

**2. "Access Denied"**
- Verify user has admin role
- Check JWT token validity
- Confirm RBAC middleware active

**3. "Scan returns no results"**
- Database may have no old records
- Verify retention period configuration
- Check date calculations in backend

**4. Component doesn't render**
- Check for TypeScript errors
- Verify imports are correct
- Check console for React errors
- Ensure all dependencies installed

### Debug Mode

```typescript
// Enable debug logging
const handleScan = async () => {
  console.log('Starting scan...');
  try {
    const results = await apiClient.scanRetention(true);
    console.log('Scan results:', results);
  } catch (error) {
    console.error('Scan error:', error);
  }
};
```

## Deployment

### Environment Variables

```env
NEXT_PUBLIC_API_URL=https://api.tutormax.com
```

### Build and Deploy

```bash
# Install dependencies
npm install

# Type check
npm run type-check

# Build for production
npm run build

# Start production server
npm start
```

### Production Checklist

- [ ] Environment variables configured
- [ ] API base URL set correctly
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Error tracking enabled (Sentry, etc.)
- [ ] Analytics configured
- [ ] Admin users created
- [ ] Training documentation provided

## Support

### Documentation Links

- [Backend API Documentation](./DATA_RETENTION_SYSTEM.md)
- [FERPA Compliance](./FERPA_COMPLIANCE.md)
- [GDPR Compliance](./GDPR_COMPLIANCE.md)
- [Implementation Summary](./TASK_20_IMPLEMENTATION_SUMMARY.md)

### Getting Help

1. Check console for errors
2. Review API response in Network tab
3. Verify backend logs
4. Contact development team

## Changelog

### Version 1.0.0 (2025-11-09)

**Initial Release:**
- ✅ Data retention dashboard
- ✅ Retention scan interface
- ✅ Compliance reporting
- ✅ Policy viewer
- ✅ GDPR deletion support
- ✅ API client integration
- ✅ TypeScript type definitions
- ✅ RBAC enforcement
- ✅ Error handling
- ✅ Responsive design

**Pending:**
- Advanced archival management UI
- Enhanced GDPR deletion workflow
- Chart visualizations
- Export functionality
- Real-time updates

---

**Note:** This UI complements the fully functional backend system. All core retention, archival, anonymization, and deletion operations are operational via API or CLI even without the UI.
