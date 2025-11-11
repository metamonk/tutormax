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
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-muted/20 to-background p-4">
        <Card className="w-full max-w-3xl shadow-2xl border-2">
          <CardHeader className="text-center space-y-6 pb-8 pt-10">
            <div className="flex items-center justify-center mb-2">
              <div className="relative">
                <div className="absolute inset-0 blur-2xl bg-primary/20 animate-pulse"></div>
                <div className="relative rounded-full bg-primary/10 p-6">
                  <svg
                    className="h-16 w-16 text-primary"
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
            </div>
            <div className="space-y-3">
              <CardTitle className="text-4xl font-bold tracking-tight">TutorMax</CardTitle>
              <CardDescription className="text-xl font-medium">
                Tutor Performance Evaluation & Analytics Platform
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-8 pb-10">
            <p className="text-center text-lg text-muted-foreground max-w-2xl mx-auto">
              Real-time monitoring and analytics for tutor performance, with actionable insights
              and AI-powered intervention recommendations.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => router.push('/login')}
                className="text-lg h-12 px-8 shadow-lg hover:shadow-xl transition-shadow"
              >
                Sign In
                <svg
                  className="ml-2 h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                  />
                </svg>
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => router.push('/dashboard')}
                className="text-lg h-12 px-8 border-2"
              >
                View Demo Dashboard
              </Button>
            </div>
            <div className="border-t-2 pt-8 mt-8">
              <h3 className="text-xl font-bold mb-6 text-center">Key Features</h3>
              <ul className="grid sm:grid-cols-2 gap-4 max-w-2xl mx-auto">
                <li className="flex items-start gap-3 p-4 rounded-lg bg-muted/50 border">
                  <div className="rounded-full bg-success/10 p-1.5 mt-0.5">
                    <svg className="h-5 w-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-base font-medium">Real-time tutor performance metrics and alerts</span>
                </li>
                <li className="flex items-start gap-3 p-4 rounded-lg bg-muted/50 border">
                  <div className="rounded-full bg-success/10 p-1.5 mt-0.5">
                    <svg className="h-5 w-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-base font-medium">AI-powered churn prediction and intervention recommendations</span>
                </li>
                <li className="flex items-start gap-3 p-4 rounded-lg bg-muted/50 border">
                  <div className="rounded-full bg-success/10 p-1.5 mt-0.5">
                    <svg className="h-5 w-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-base font-medium">Role-based access control for admins, operations, and tutors</span>
                </li>
                <li className="flex items-start gap-3 p-4 rounded-lg bg-muted/50 border">
                  <div className="rounded-full bg-success/10 p-1.5 mt-0.5">
                    <svg className="h-5 w-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-base font-medium">Comprehensive analytics dashboard with visualizations</span>
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/20 to-background">
      <div className="container mx-auto py-10 px-4">
        <Card className="mb-8 border-2 shadow-lg">
          <CardHeader className="pb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="space-y-2">
                <CardTitle className="text-3xl font-bold tracking-tight">
                  Welcome, {user?.full_name}!
                </CardTitle>
                <CardDescription className="text-base">{user?.email}</CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={handleLogout}
                className="border-2 self-start sm:self-center"
              >
                Sign Out
                <svg
                  className="ml-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  />
                </svg>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <h3 className="text-base font-semibold">Your Roles</h3>
              <div className="flex flex-wrap gap-2">
                {user?.roles.map((role) => {
                  const roleInfo = ROLE_DEFINITIONS[role];
                  return (
                    <Badge
                      key={role}
                      style={{ backgroundColor: roleInfo.color }}
                      className="text-white px-3 py-1 text-sm font-medium"
                    >
                      {roleInfo.label}
                    </Badge>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold tracking-tight mb-6">Quick Access</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card
            className="hover:shadow-xl hover:scale-[1.02] transition-all cursor-pointer border-2 group"
            onClick={() => router.push('/dashboard')}
          >
            <CardHeader className="space-y-3">
              <div className="rounded-full bg-primary/10 w-12 h-12 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <div className="space-y-1">
                <CardTitle className="text-xl">Dashboard</CardTitle>
                <CardDescription className="text-base">View real-time metrics and analytics</CardDescription>
              </div>
            </CardHeader>
          </Card>

          {hasRole('admin') && (
            <Card
              className="hover:shadow-xl hover:scale-[1.02] transition-all cursor-pointer border-2 group"
              onClick={() => router.push('/users')}
            >
              <CardHeader className="space-y-3">
                <div className="rounded-full bg-primary/10 w-12 h-12 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                    />
                  </svg>
                </div>
                <div className="space-y-1">
                  <CardTitle className="text-xl">User Management</CardTitle>
                  <CardDescription className="text-base">Manage users and permissions</CardDescription>
                </div>
              </CardHeader>
            </Card>
          )}

          {(hasRole('tutor') || hasRole('admin')) && (
            <Card
              className="hover:shadow-xl hover:scale-[1.02] transition-all cursor-pointer border-2 group"
              onClick={() => router.push('/tutor-portal')}
            >
              <CardHeader className="space-y-3">
                <div className="rounded-full bg-primary/10 w-12 h-12 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
                <div className="space-y-1">
                  <CardTitle className="text-xl">Tutor Portal</CardTitle>
                  <CardDescription className="text-base">View your performance and training</CardDescription>
                </div>
              </CardHeader>
            </Card>
          )}

          {hasRole('admin') && (
            <>
              <Card
                className="hover:shadow-xl hover:scale-[1.02] transition-all cursor-pointer border-2 group"
                onClick={() => router.push('/admin/audit-logs')}
              >
                <CardHeader className="space-y-3">
                  <div className="rounded-full bg-primary/10 w-12 h-12 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                    <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <div className="space-y-1">
                    <CardTitle className="text-xl">Audit Logs</CardTitle>
                    <CardDescription className="text-base">View system audit logs</CardDescription>
                  </div>
                </CardHeader>
              </Card>

              <Card
                className="hover:shadow-xl hover:scale-[1.02] transition-all cursor-pointer border-2 group"
                onClick={() => router.push('/admin/compliance')}
              >
                <CardHeader className="space-y-3">
                  <div className="rounded-full bg-primary/10 w-12 h-12 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                    <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                      />
                    </svg>
                  </div>
                  <div className="space-y-1">
                    <CardTitle className="text-xl">Compliance</CardTitle>
                    <CardDescription className="text-base">FERPA, COPPA, GDPR reports</CardDescription>
                  </div>
                </CardHeader>
              </Card>

              <Card
                className="hover:shadow-xl hover:scale-[1.02] transition-all cursor-pointer border-2 group"
                onClick={() => router.push('/admin/training')}
              >
                <CardHeader className="space-y-3">
                  <div className="rounded-full bg-primary/10 w-12 h-12 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                    <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                      />
                    </svg>
                  </div>
                  <div className="space-y-1">
                    <CardTitle className="text-xl">Training</CardTitle>
                    <CardDescription className="text-base">Manage training modules</CardDescription>
                  </div>
                </CardHeader>
              </Card>
            </>
          )}
          </div>
        </div>
      </div>
    </div>
  );
}
