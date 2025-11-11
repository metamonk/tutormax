"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { StudentFeedbackForm } from "@/components/feedback";
import { apiClient } from "@/lib/api";
import { FeedbackTokenValidation } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle, XCircle } from "lucide-react";

export default function FeedbackPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const [isValidating, setIsValidating] = useState(true);
  const [tokenValidation, setTokenValidation] = useState<FeedbackTokenValidation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [alreadySubmitted, setAlreadySubmitted] = useState(false);

  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setError("Invalid feedback link");
        setIsValidating(false);
        return;
      }

      try {
        const validation = await apiClient.validateFeedbackToken(token);

        if (!validation.valid) {
          setError(validation.message || "This feedback link is invalid or has expired");
          setIsValidating(false);
          return;
        }

        setTokenValidation(validation);
      } catch (err: any) {
        if (err.response?.status === 400 && err.response?.data?.detail?.includes("already submitted")) {
          setAlreadySubmitted(true);
        } else {
          setError("Failed to validate feedback link. Please try again.");
        }
      } finally {
        setIsValidating(false);
      }
    };

    validateToken();
  }, [token]);

  const handleSuccess = () => {
    // Success message is handled by the form component
    // You could optionally redirect after a delay
    setTimeout(() => {
      // router.push('/'); // Redirect to home or a thank you page
    }, 3000);
  };

  if (isValidating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-muted/20 to-background p-4">
        <Card className="w-full max-w-md border-2 shadow-lg">
          <CardContent className="pt-8 pb-8">
            <div className="flex flex-col items-center justify-center space-y-6">
              <div className="relative">
                <div className="absolute inset-0 blur-xl bg-primary/20 animate-pulse"></div>
                <Loader2 className="relative h-16 w-16 animate-spin text-primary" />
              </div>
              <div className="text-center space-y-2">
                <p className="text-xl font-semibold">Validating feedback link</p>
                <p className="text-sm text-muted-foreground">Please wait a moment...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (alreadySubmitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-muted/20 to-background p-4">
        <Card className="w-full max-w-md border-2 shadow-lg">
          <CardHeader className="text-center pb-8 pt-8">
            <div className="flex items-center justify-center mb-6">
              <div className="rounded-full bg-warning/10 p-4">
                <AlertCircle className="h-16 w-16 text-warning" />
              </div>
            </div>
            <CardTitle className="text-2xl mb-3">Feedback Already Submitted</CardTitle>
            <CardDescription className="text-base">
              You have already submitted feedback for this session. Thank you for your input!
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (error || !tokenValidation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-muted/20 to-background p-4">
        <Card className="w-full max-w-md border-2 shadow-lg">
          <CardHeader className="text-center pb-6 pt-8">
            <div className="flex items-center justify-center mb-6">
              <div className="rounded-full bg-destructive/10 p-4">
                <XCircle className="h-16 w-16 text-destructive" />
              </div>
            </div>
            <CardTitle className="text-2xl mb-3">Invalid Feedback Link</CardTitle>
            <CardDescription className="text-base">
              {error || "This feedback link is invalid or has expired."}
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-8">
            <Alert variant="destructive" className="border-2">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Please check your email for the correct feedback link or contact support if you
                continue to have issues.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/20 to-background p-4 py-12">
      <div className="container mx-auto max-w-4xl">
        <div className="text-center mb-10 space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
            <svg
              className="w-8 h-8 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
              />
            </svg>
          </div>
          <h1 className="text-4xl font-bold tracking-tight">Share Your Feedback</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Help us improve by sharing your experience with this tutoring session. Your honest feedback helps us provide better support.
          </p>
        </div>

        <StudentFeedbackForm
          token={token}
          sessionInfo={{
            tutor_name: tokenValidation.tutor_name,
            session_date: tokenValidation.session_date
              ? new Date(tokenValidation.session_date).toLocaleDateString("en-US", {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : undefined,
            subject: tokenValidation.subject,
          }}
          requiresParentConsent={tokenValidation.requires_parent_consent || false}
          isUnder13={tokenValidation.is_under_13 || false}
          onSuccess={handleSuccess}
        />

        {/* Privacy Notice */}
        <Card className="mt-10 border-2 bg-muted/30">
          <CardContent className="pt-6 pb-6">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-primary/10 p-2 mt-0.5">
                <svg
                  className="w-4 h-4 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium mb-1">Your Privacy Matters</p>
                <p className="text-sm text-muted-foreground">
                  Your feedback is confidential and will be used solely to improve our tutoring services.{" "}
                  <a href="/privacy" className="text-primary hover:underline font-medium">
                    Read our Privacy Policy
                  </a>
                  {" "}for more information.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
