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
              </CardContent>

              <CardFooter className="flex flex-col space-y-4">
                <div className="text-sm text-muted-foreground border-t pt-4 w-full">
                  <p className="font-semibold mb-2">Admin credentials:</p>
                  <div className="space-y-1.5 text-xs bg-muted/50 rounded-lg p-3">
                    <div className="space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Email:</span>
                        <code className="font-mono">admin@tutormax.com</code>
                      </div>
                      <div className="flex justify-between items-center pl-4 text-[11px]">
                        <span className="text-muted-foreground/70">Password:</span>
                        <code className="font-mono">Admin123456</code>
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
