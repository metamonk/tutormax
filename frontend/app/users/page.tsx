'use client';

import { useState, useEffect } from 'react';
import { useAuth, RequireRole } from '@/contexts';
import { apiClient } from '@/lib/api';
import type { User, UserRole, RegisterRequest, UserUpdateRequest } from '@/lib/types';
import { ROLE_DEFINITIONS } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { RoleAssignmentDialog } from '@/components/admin/RoleAssignment';

function RoleBadge({ roles }: { roles: UserRole[] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {roles.map((role) => {
        const roleInfo = ROLE_DEFINITIONS[role];
        return (
          <Badge
            key={role}
            style={{ backgroundColor: roleInfo.color }}
            className="text-white"
            title={roleInfo.description}
          >
            {roleInfo.label}
          </Badge>
        );
      })}
    </div>
  );
}

interface UserFormProps {
  user?: User;
  onSubmit: (data: RegisterRequest | UserUpdateRequest) => Promise<void>;
  onCancel: () => void;
}

function UserForm({ user, onSubmit, onCancel }: UserFormProps) {
  const [formData, setFormData] = useState({
    email: user?.email || '',
    full_name: user?.full_name || '',
    password: '',
    roles: user?.roles || [] as UserRole[],
    is_active: user?.is_active ?? true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const submitData: any = {
        email: formData.email,
        full_name: formData.full_name,
        roles: formData.roles,
        is_active: formData.is_active,
      };

      if (!user || formData.password) {
        if (!user && !formData.password) {
          setError('Password is required for new users');
          setLoading(false);
          return;
        }
        if (formData.password) {
          submitData.password = formData.password;
        }
      }

      await onSubmit(submitData);
      toast.success(user ? 'User updated successfully' : 'User created successfully');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to save user';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const toggleRole = (role: UserRole) => {
    setFormData((prev) => ({
      ...prev,
      roles: prev.roles.includes(role)
        ? prev.roles.filter((r) => r !== role)
        : [...prev.roles, role],
    }));
  };

  const allRoles: UserRole[] = ['admin', 'operations_manager', 'people_ops', 'tutor', 'student'];

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <Label htmlFor="email">Email *</Label>
        <Input
          id="email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          disabled={loading || !!user}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="full_name">Full Name *</Label>
        <Input
          id="full_name"
          type="text"
          value={formData.full_name}
          onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
          disabled={loading}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">
          Password {user ? '(leave blank to keep current)' : '*'}
        </Label>
        <Input
          id="password"
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          disabled={loading}
          required={!user}
        />
      </div>

      <div className="space-y-2">
        <Label>Roles *</Label>
        <div className="flex flex-wrap gap-2">
          {allRoles.map((role) => {
            const roleInfo = ROLE_DEFINITIONS[role];
            const isSelected = formData.roles.includes(role);
            return (
              <Button
                key={role}
                type="button"
                variant={isSelected ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleRole(role)}
                disabled={loading}
                style={isSelected ? { backgroundColor: roleInfo.color } : {}}
              >
                {roleInfo.label}
              </Button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="is_active"
          checked={formData.is_active}
          onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          disabled={loading}
          className="rounded border-gray-300"
        />
        <Label htmlFor="is_active" className="cursor-pointer">
          Active
        </Label>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Saving...' : user ? 'Update User' : 'Create User'}
        </Button>
      </DialogFooter>
    </form>
  );
}

export default function UsersPage() {
  const { hasRole } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | undefined>();
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [bulkImportOpen, setBulkImportOpen] = useState(false);
  const [passwordResetOpen, setPasswordResetOpen] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getUsers();
      setUsers(data);
    } catch (err) {
      toast.error('Failed to load users');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      searchTerm === '' ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.full_name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesRole = roleFilter === 'all' || user.roles.includes(roleFilter);

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && user.is_active) ||
      (statusFilter === 'inactive' && !user.is_active);

    return matchesSearch && matchesRole && matchesStatus;
  });

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, roleFilter, statusFilter]);

  // Calculate pagination
  const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedUsers = filteredUsers.slice(startIndex, endIndex);

  const handleCreateOrUpdate = async (data: RegisterRequest | UserUpdateRequest) => {
    if (selectedUser) {
      await apiClient.updateUser(selectedUser.id, data as UserUpdateRequest);
    } else {
      await apiClient.createUser(data as RegisterRequest);
    }
    await loadUsers();
    setDialogOpen(false);
    setSelectedUser(undefined);
  };

  const handleDelete = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      await apiClient.deleteUser(userId);
      toast.success('User deleted successfully');
      await loadUsers();
    } catch (err) {
      toast.error('Failed to delete user');
      console.error(err);
    }
  };

  const handleToggleActive = async (user: User) => {
    const action = user.is_active ? 'deactivate' : 'activate';
    if (!confirm(`Are you sure you want to ${action} ${user.email}?`)) return;

    try {
      await apiClient.updateUser(user.id, { is_active: !user.is_active });
      toast.success(`User ${action}d successfully`);
      await loadUsers();
    } catch (err) {
      toast.error(`Failed to ${action} user`);
      console.error(err);
    }
  };

  const handlePasswordReset = async (userId: number, newPassword: string) => {
    try {
      const response = await fetch(`/api/admin/users/${userId}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ new_password: newPassword }),
      });

      if (!response.ok) throw new Error('Failed to reset password');

      toast.success('Password reset successfully');
      setPasswordResetOpen(false);
      setSelectedUser(undefined);
    } catch (err) {
      toast.error('Failed to reset password');
      console.error(err);
    }
  };

  const handleBulkImport = async (csvFile: File) => {
    try {
      const formData = new FormData();
      formData.append('file', csvFile);

      const response = await fetch('/api/admin/users/bulk-import', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to import users');

      const result = await response.json();
      toast.success(`Successfully imported ${result.imported_count} users`);
      setBulkImportOpen(false);
      await loadUsers();
    } catch (err) {
      toast.error('Failed to import users');
      console.error(err);
    }
  };

  const openCreateDialog = () => {
    setSelectedUser(undefined);
    setDialogOpen(true);
  };

  const openEditDialog = (user: User) => {
    setSelectedUser(user);
    setDialogOpen(true);
  };

  const openPasswordReset = (user: User) => {
    setSelectedUser(user);
    setPasswordResetOpen(true);
  };

  return (
    <RequireRole roles={['admin']}>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="container mx-auto py-8 px-4 space-y-6">
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="transition-card hover-lift">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{users.length}</div>
              </CardContent>
            </Card>
            <Card className="transition-card hover-lift">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Active Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-success">{users.filter(u => u.is_active).length}</div>
              </CardContent>
            </Card>
            <Card className="transition-card hover-lift">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Inactive Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-muted-foreground">{users.filter(u => !u.is_active).length}</div>
              </CardContent>
            </Card>
            <Card className="transition-card hover-lift">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Filtered Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary">{filteredUsers.length}</div>
              </CardContent>
            </Card>
          </div>

          {/* Main User Management Card */}
          <Card className="shadow-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-2xl font-bold">User Management</CardTitle>
                  <CardDescription className="mt-1">Manage user accounts, roles, and permissions</CardDescription>
                </div>
                <div className="flex gap-2">
                <Button variant="outline" onClick={() => setBulkImportOpen(true)}>
                  <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Import Users
                </Button>
                <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                  <DialogTrigger asChild>
                    <Button onClick={openCreateDialog}>
                      <svg
                        className="mr-2 h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 4v16m8-8H4"
                        />
                      </svg>
                      Create User
                    </Button>
                  </DialogTrigger>
                <DialogContent className="sm:max-w-[525px]">
                  <DialogHeader>
                    <DialogTitle>
                      {selectedUser ? 'Edit User' : 'Create New User'}
                    </DialogTitle>
                    <DialogDescription>
                      {selectedUser
                        ? 'Update user information and roles'
                        : 'Add a new user to the system'}
                    </DialogDescription>
                  </DialogHeader>
                  <UserForm
                    user={selectedUser}
                    onSubmit={handleCreateOrUpdate}
                    onCancel={() => setDialogOpen(false)}
                  />
                </DialogContent>
              </Dialog>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Enhanced Filters */}
            <div className="bg-muted/30 p-4 rounded-lg border border-border">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="search" className="text-sm font-semibold">Search Users</Label>
                  <div className="relative">
                    <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <Input
                      id="search"
                      placeholder="Search by name or email..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role-filter" className="text-sm font-semibold">Filter by Role</Label>
                  <select
                    id="role-filter"
                    className="w-full px-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value as UserRole | 'all')}
                  >
                    <option value="all">All Roles</option>
                    <option value="admin">Admin</option>
                    <option value="operations_manager">Operations Manager</option>
                    <option value="people_ops">People Ops</option>
                    <option value="tutor">Tutor</option>
                    <option value="student">Student</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="status-filter" className="text-sm font-semibold">Filter by Status</Label>
                  <select
                    id="status-filter"
                    className="w-full px-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')}
                  >
                    <option value="all">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
              </div>

              {/* Results count with clear filters button */}
              <div className="mt-4 flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Showing <span className="font-semibold text-foreground">{filteredUsers.length}</span> of <span className="font-semibold text-foreground">{users.length}</span> users
                </div>
                {(searchTerm || roleFilter !== 'all' || statusFilter !== 'all') && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSearchTerm('');
                      setRoleFilter('all');
                      setStatusFilter('all');
                    }}
                  >
                    Clear filters
                  </Button>
                )}
              </div>
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                <div className="text-muted-foreground">Loading users...</div>
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-4 text-center">
                <svg className="h-16 w-16 text-muted-foreground opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <div>
                  <div className="font-semibold text-lg mb-1">No users found</div>
                  <div className="text-sm text-muted-foreground">Try adjusting your search or filter criteria</div>
                </div>
                {(searchTerm || roleFilter !== 'all' || statusFilter !== 'all') && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSearchTerm('');
                      setRoleFilter('all');
                      setStatusFilter('all');
                    }}
                  >
                    Clear all filters
                  </Button>
                )}
              </div>
            ) : (
              <>
                <div className="rounded-lg border border-border overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-muted/50">
                        <TableHead className="font-semibold">Email</TableHead>
                        <TableHead className="font-semibold">Name</TableHead>
                        <TableHead className="font-semibold">Roles</TableHead>
                        <TableHead className="font-semibold">Status</TableHead>
                        <TableHead className="text-right font-semibold">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paginatedUsers.map((user) => (
                        <TableRow key={user.id} className="transition-colors hover:bg-muted/30">
                          <TableCell className="font-medium">{user.email}</TableCell>
                          <TableCell>{user.full_name}</TableCell>
                          <TableCell>
                            <RoleBadge roles={user.roles} />
                          </TableCell>
                          <TableCell>
                            {user.is_active ? (
                              <Badge variant="outline" className="bg-success/10 text-success border-success/20 font-medium">
                                Active
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="bg-muted text-muted-foreground border-muted-foreground/20 font-medium">
                                Inactive
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                          <RoleAssignmentDialog
                            userId={user.id}
                            currentRoles={user.roles}
                            userName={user.full_name || user.email}
                            onUpdate={async (roles) => {
                              await apiClient.updateUser(user.id, { roles });
                              await loadUsers();
                            }}
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openEditDialog(user)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant={user.is_active ? "outline" : "default"}
                            size="sm"
                            onClick={() => handleToggleActive(user)}
                          >
                            {user.is_active ? 'Deactivate' : 'Activate'}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openPasswordReset(user)}
                          >
                            Reset Password
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDelete(user.id)}
                          >
                            Delete
                          </Button>
                        </div>
                      </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {/* Enhanced Pagination Controls */}
                {filteredUsers.length > itemsPerPage && (
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4">
                    <div className="text-sm text-muted-foreground">
                      Showing <span className="font-medium text-foreground">{startIndex + 1}</span> to{' '}
                      <span className="font-medium text-foreground">{Math.min(endIndex, filteredUsers.length)}</span> of{' '}
                      <span className="font-medium text-foreground">{filteredUsers.length}</span> users
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-2">
                        <label className="text-sm text-muted-foreground">Rows per page:</label>
                        <select
                          value={itemsPerPage}
                          onChange={(e) => setItemsPerPage(Number(e.target.value))}
                          className="px-2 py-1 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        >
                          <option value={10}>10</option>
                          <option value={25}>25</option>
                          <option value={50}>50</option>
                          <option value={100}>100</option>
                        </select>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage(1)}
                          disabled={currentPage === 1}
                        >
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                          </svg>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                        >
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                          </svg>
                        </Button>
                        <div className="px-4 py-1 text-sm font-medium">
                          {currentPage} / {totalPages}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                          disabled={currentPage === totalPages}
                        >
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage(totalPages)}
                          disabled={currentPage === totalPages}
                        >
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                          </svg>
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Bulk Import Dialog */}
        <Dialog open={bulkImportOpen} onOpenChange={setBulkImportOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Bulk Import Users</DialogTitle>
              <DialogDescription>
                Upload a CSV file with columns: email, full_name, roles, is_active
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="csv-file">CSV File</Label>
                <Input
                  id="csv-file"
                  type="file"
                  accept=".csv"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      handleBulkImport(file);
                    }
                  }}
                />
              </div>
              <Alert>
                <AlertDescription>
                  <strong>CSV Format:</strong>
                  <br />
                  email,full_name,roles,is_active
                  <br />
                  john@example.com,John Doe,&quot;tutor&quot;,true
                  <br />
                  Roles can be: admin, operations_manager, people_ops, tutor, student
                </AlertDescription>
              </Alert>
            </div>
          </DialogContent>
        </Dialog>

        {/* Password Reset Dialog */}
        <Dialog open={passwordResetOpen} onOpenChange={setPasswordResetOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reset Password</DialogTitle>
              <DialogDescription>
                Reset password for {selectedUser?.email}
              </DialogDescription>
            </DialogHeader>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const password = formData.get('password') as string;
                if (selectedUser && password) {
                  handlePasswordReset(selectedUser.id, password);
                }
              }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="new-password">New Password</Label>
                <Input
                  id="new-password"
                  name="password"
                  type="password"
                  required
                  minLength={8}
                  placeholder="Enter new password"
                />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setPasswordResetOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  Reset Password
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
        </div>
      </div>
    </RequireRole>
  );
}
