'use client';

import { useState } from 'react';
import { UserRole, ROLE_DEFINITIONS } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';

interface RoleInfo {
  label: string;
  description: string;
  color: string;
  permissions: string[];
}

const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  admin: [
    'Manage all users',
    'Manage system settings',
    'Access all dashboards',
    'Audit log access',
    'Data export',
    'User creation/deletion',
  ],
  operations_manager: [
    'View tutor performance',
    'Manage interventions',
    'Access analytics dashboard',
    'Assign training',
    'View reports',
  ],
  people_ops: [
    'Manage tutor onboarding',
    'Access compliance tools',
    'View HR metrics',
    'Manage training resources',
  ],
  tutor: [
    'View own performance',
    'Access tutor portal',
    'View assigned training',
    'Manage availability',
    'View session history',
  ],
  student: [
    'Book sessions',
    'Provide feedback',
    'View session history',
    'Access learning resources',
  ],
};

interface RoleAssignmentProps {
  userId: number;
  currentRoles: UserRole[];
  userName: string;
  onUpdate: (roles: UserRole[]) => Promise<void>;
}

export function RoleAssignmentDialog({
  userId,
  currentRoles,
  userName,
  onUpdate,
}: RoleAssignmentProps) {
  const [open, setOpen] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState<UserRole[]>(currentRoles);
  const [loading, setLoading] = useState(false);

  const handleToggleRole = (role: UserRole) => {
    setSelectedRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]
    );
  };

  const handleSave = async () => {
    if (selectedRoles.length === 0) {
      toast.error('User must have at least one role');
      return;
    }

    setLoading(true);
    try {
      await onUpdate(selectedRoles);
      toast.success('Roles updated successfully');
      setOpen(false);
    } catch (error) {
      toast.error('Failed to update roles');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedRoles(currentRoles);
  };

  const allRoles: UserRole[] = ['admin', 'operations_manager', 'people_ops', 'tutor', 'student'];

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
        Manage Roles
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Manage Roles for {userName}</DialogTitle>
            <DialogDescription>
              Assign or remove roles to control user permissions and access levels.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Current Roles Summary */}
            <div className="rounded-lg bg-gray-50 p-4">
              <h4 className="font-medium text-sm mb-2">Current Roles</h4>
              <div className="flex flex-wrap gap-2">
                {currentRoles.length > 0 ? (
                  currentRoles.map((role) => {
                    const roleInfo = ROLE_DEFINITIONS[role];
                    return (
                      <Badge
                        key={role}
                        style={{ backgroundColor: roleInfo.color }}
                        className="text-white"
                      >
                        {roleInfo.label}
                      </Badge>
                    );
                  })
                ) : (
                  <span className="text-sm text-gray-500">No roles assigned</span>
                )}
              </div>
            </div>

            {/* Role Selection */}
            <div className="space-y-4">
              <h4 className="font-medium text-sm">Select Roles</h4>
              {allRoles.map((role) => {
                const roleInfo = ROLE_DEFINITIONS[role];
                const isSelected = selectedRoles.includes(role);
                const permissions = ROLE_PERMISSIONS[role];

                return (
                  <Card
                    key={role}
                    className={`cursor-pointer transition-all ${
                      isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                    }`}
                    onClick={() => handleToggleRole(role)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                              isSelected
                                ? 'bg-blue-500 border-blue-500'
                                : 'border-gray-300'
                            }`}
                          >
                            {isSelected && (
                              <svg
                                className="w-3 h-3 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={3}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                            )}
                          </div>
                          <div>
                            <CardTitle className="text-base">{roleInfo.label}</CardTitle>
                            <CardDescription className="text-xs">
                              {roleInfo.description}
                            </CardDescription>
                          </div>
                        </div>
                        <Badge
                          style={{ backgroundColor: roleInfo.color }}
                          className="text-white text-xs"
                        >
                          {role}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="text-xs text-gray-600">
                        <div className="font-medium mb-1">Permissions:</div>
                        <ul className="list-disc list-inside space-y-0.5 ml-2">
                          {permissions.map((permission, idx) => (
                            <li key={idx}>{permission}</li>
                          ))}
                        </ul>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Changes Summary */}
            {JSON.stringify(selectedRoles.sort()) !== JSON.stringify(currentRoles.sort()) && (
              <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-4">
                <h4 className="font-medium text-sm text-yellow-800 mb-2">Changes Preview</h4>
                <div className="text-xs space-y-2">
                  {currentRoles
                    .filter((role) => !selectedRoles.includes(role))
                    .map((role) => (
                      <div key={role} className="text-red-700">
                        - Removing: {ROLE_DEFINITIONS[role].label}
                      </div>
                    ))}
                  {selectedRoles
                    .filter((role) => !currentRoles.includes(role))
                    .map((role) => (
                      <div key={role} className="text-green-700">
                        + Adding: {ROLE_DEFINITIONS[role].label}
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleReset} disabled={loading}>
              Reset
            </Button>
            <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={loading || selectedRoles.length === 0}>
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
