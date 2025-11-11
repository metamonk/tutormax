'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { GraduationCap, Eye, EyeOff, Loader2, CheckCircle2, Users, TrendingUp, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function LoginPage() {
  const router = useRouter();
  const { login, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [shake, setShake] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!email || !password) {
      setLocalError('Please enter both email and password');
      setShake(true);
      setTimeout(() => setShake(false), 500);
      return;
    }

    try {
      await login({ username: email, password });
      toast.success('Welcome back!');
      router.push('/dashboard');
    } catch (err: any) {
      const errorMessage = err.message || 'Invalid email or password';
      setLocalError(errorMessage);
      setShake(true);
      setTimeout(() => setShake(false), 500);
      toast.error(errorMessage);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/20 to-background">
      <div className="container mx-auto flex min-h-screen items-center justify-center p-4">
        <div className="grid w-full max-w-6xl gap-8 lg:grid-cols-2 lg:gap-12">
          {/* Branding Section - Hidden on mobile */}
          <div className="hidden lg:flex lg:flex-col lg:justify-center space-y-8">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg">
                  <GraduationCap className="h-7 w-7 text-primary-foreground" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">TutorMax</h1>
                  <p className="text-sm text-muted-foreground">Empowering Tutors, Enhancing Learning</p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold mb-4">Trusted by educators worldwide</h2>
                <p className="text-muted-foreground text-lg">
                  Real-time performance tracking and analytics to help tutors excel and students succeed.
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-success/10">
                    <TrendingUp className="h-5 w-5 text-success" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Performance Analytics</h3>
                    <p className="text-sm text-muted-foreground">
                      Track and improve tutor performance with real-time insights
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <Users className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Role-Based Access</h3>
                    <p className="text-sm text-muted-foreground">
                      Secure access control for admins, operations, and tutors
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-warning/10">
                    <Shield className="h-5 w-5 text-warning" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Enterprise Security</h3>
                    <p className="text-sm text-muted-foreground">
                      FERPA, COPPA, and GDPR compliant data protection
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border bg-card/50 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="h-5 w-5 text-success" />
                  <span className="font-semibold">Join 10,000+ educators</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Trusted by schools and tutoring organizations worldwide to deliver exceptional learning outcomes.
                </p>
              </div>
            </div>
          </div>

          {/* Login Form */}
          <div className="flex items-center justify-center">
            <Card
              className={cn(
                'w-full max-w-md shadow-xl transition-all duration-200',
                shake && 'animate-shake'
              )}
            >
              <CardHeader className="space-y-1 text-center">
                {/* Mobile Logo */}
                <div className="flex items-center justify-center mb-4 lg:hidden">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg">
                    <GraduationCap className="h-7 w-7 text-primary-foreground" />
                  </div>
                </div>
                <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
                <CardDescription>Sign in to your TutorMax account</CardDescription>
              </CardHeader>

              <CardContent>
                {localError && (
                  <div className="mb-4 rounded-lg bg-destructive/10 border border-destructive/20 p-3 animate-in fade-in slide-in-from-top-1 duration-200">
                    <p className="text-sm text-destructive font-medium">{localError}</p>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="your.email@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={loading}
                      required
                      autoComplete="email"
                      className="transition-all duration-200"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="password">Password</Label>
                      <button
                        type="button"
                        className="text-sm text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded px-1"
                        tabIndex={-1}
                      >
                        Forgot password?
                      </button>
                    </div>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        disabled={loading}
                        required
                        autoComplete="current-password"
                        className="pr-10 transition-all duration-200"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
                        tabIndex={-1}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="remember"
                      checked={rememberMe}
                      onCheckedChange={(checked) => setRememberMe(checked as boolean)}
                      disabled={loading}
                    />
                    <Label
                      htmlFor="remember"
                      className="text-sm font-normal cursor-pointer"
                    >
                      Remember me
                    </Label>
                  </div>

                  <Button
                    type="submit"
                    className="w-full transition-all duration-200"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Signing in...
                      </>
                    ) : (
                      'Sign In'
                    )}
                  </Button>
                </form>

                {/* Divider */}
                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
                  </div>
                </div>

                {/* Google Sign In - Placeholder */}
                <Button
                  type="button"
                  variant="outline"
                  className="w-full transition-all duration-200"
                  disabled
                >
                  <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Sign in with Google
                </Button>
              </CardContent>

              <CardFooter className="flex flex-col space-y-4">
                <div className="text-sm text-muted-foreground border-t pt-4 w-full">
                  <p className="font-semibold mb-2">Demo accounts for testing:</p>
                  <div className="space-y-1.5 text-xs bg-muted/50 rounded-lg p-3">
                    <div className="space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Admin:</span>
                        <code className="font-mono">admin@tutormax.com</code>
                      </div>
                      <div className="flex justify-between items-center pl-4 text-[11px]">
                        <span className="text-muted-foreground/70">Password:</span>
                        <code className="font-mono">admin123</code>
                      </div>
                    </div>
                    <div className="space-y-1 pt-1">
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Tutor:</span>
                        <code className="font-mono">tutor@tutormax.com</code>
                      </div>
                      <div className="flex justify-between items-center pl-4 text-[11px]">
                        <span className="text-muted-foreground/70">Password:</span>
                        <code className="font-mono">tutor123</code>
                      </div>
                    </div>
                    <div className="space-y-1 pt-1">
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Student:</span>
                        <code className="font-mono">student@tutormax.com</code>
                      </div>
                      <div className="flex justify-between items-center pl-4 text-[11px]">
                        <span className="text-muted-foreground/70">Password:</span>
                        <code className="font-mono">student123</code>
                      </div>
                    </div>
                  </div>
                </div>
              </CardFooter>
            </Card>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
          20%, 40%, 60%, 80% { transform: translateX(4px); }
        }
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
      `}</style>
    </div>
  );
}
