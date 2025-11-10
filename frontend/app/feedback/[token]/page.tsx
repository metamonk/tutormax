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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
              <p className="text-lg text-gray-600">Validating feedback link...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (alreadySubmitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center justify-center mb-4">
              <AlertCircle className="h-12 w-12 text-yellow-600" />
            </div>
            <CardTitle className="text-center">Feedback Already Submitted</CardTitle>
            <CardDescription className="text-center">
              You have already submitted feedback for this session. Thank you for your input!
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (error || !tokenValidation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center justify-center mb-4">
              <XCircle className="h-12 w-12 text-red-600" />
            </div>
            <CardTitle className="text-center">Invalid Feedback Link</CardTitle>
            <CardDescription className="text-center">
              {error || "This feedback link is invalid or has expired."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
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
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-4 py-8">
      <div className="container mx-auto max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Share Your Feedback</h1>
          <p className="text-gray-600">
            Help us improve by sharing your experience with this tutoring session
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
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Your feedback is confidential and will be used to improve our tutoring services.
            <br />
            Read our{" "}
            <a href="/privacy" className="text-blue-600 hover:underline">
              Privacy Policy
            </a>{" "}
            for more information.
          </p>
        </div>
      </div>
    </div>
  );
}
