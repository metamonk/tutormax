'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ROLE_DEFINITIONS } from '@/lib/types';

export default function Home() {
  const router = useRouter();
  const { user, isAuthenticated, logout, hasRole } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-4">
        <Card className="w-full max-w-2xl shadow-xl">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center mb-4">
              <div className="rounded-full bg-blue-100 dark:bg-blue-900 p-4">
                <svg
                  className="h-12 w-12 text-blue-600 dark:text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
            </div>
            <CardTitle className="text-3xl font-bold">TutorMax</CardTitle>
            <CardDescription className="text-lg">
              Tutor Performance Evaluation & Analytics Platform
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-center text-muted-foreground">
              Real-time monitoring and analytics for tutor performance, with actionable insights
              and intervention recommendations.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" onClick={() => router.push('/login')}>
                Sign In
              </Button>
              <Button size="lg" variant="outline" onClick={() => router.push('/dashboard')}>
                View Demo Dashboard
              </Button>
            </div>
            <div className="border-t pt-6 mt-6">
              <h3 className="font-semibold mb-3 text-center">Key Features:</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Real-time tutor performance metrics and alerts
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  AI-powered churn prediction and intervention recommendations
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Role-based access control for admins, operations, and tutors
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Comprehensive analytics dashboard with visualizations
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto py-8 px-4">
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl">Welcome, {user?.full_name}!</CardTitle>
                <CardDescription>You are signed in as {user?.email}</CardDescription>
              </div>
              <Button variant="outline" onClick={handleLogout}>
                Sign Out
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Your Roles:</h3>
                <div className="flex flex-wrap gap-2">
                  {user?.roles.map((role) => {
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
                  })}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/dashboard')}>
            <CardHeader>
              <CardTitle className="flex items-center">
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Dashboard
              </CardTitle>
              <CardDescription>View real-time metrics and analytics</CardDescription>
            </CardHeader>
          </Card>

          {hasRole('admin') && (
            <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/users')}>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  User Management
                </CardTitle>
                <CardDescription>Manage users and permissions</CardDescription>
              </CardHeader>
            </Card>
          )}

          {(hasRole('tutor') || hasRole('admin')) && (
            <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/tutor-portal')}>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Tutor Portal
                </CardTitle>
                <CardDescription>View your performance and training</CardDescription>
              </CardHeader>
            </Card>
          )}

          {hasRole('admin') && (
            <>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/admin/audit-logs')}>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Audit Logs
                  </CardTitle>
                  <CardDescription>View system audit logs</CardDescription>
                </CardHeader>
              </Card>

              <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/admin/compliance')}>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    Compliance
                  </CardTitle>
                  <CardDescription>FERPA, COPPA, GDPR reports</CardDescription>
                </CardHeader>
              </Card>

              <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/admin/training')}>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    Training
                  </CardTitle>
                  <CardDescription>Manage training modules</CardDescription>
                </CardHeader>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
