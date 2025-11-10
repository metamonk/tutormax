"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Rating, RatingButton } from "@/components/kibo-ui/rating";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiClient } from "@/lib/api";
import { IMPROVEMENT_AREAS } from "@/lib/types";
import { CheckCircle2, Loader2, AlertCircle } from "lucide-react";

const feedbackSchema = z.object({
  sessionRating: z.number().min(1, "Please rate the session").max(5),
  tutorHelpfulness: z.number().min(1, "Please rate tutor helpfulness").max(5),
  contentClarity: z.number().min(1, "Please rate content clarity").max(5),
  subjectKnowledge: z.number().min(1, "Please rate subject knowledge").max(5),
  communication: z.number().min(1, "Please rate communication").max(5),
  wouldRecommend: z.enum(["yes", "no"], {
    message: "Please select an option",
  }),
  comments: z.string().max(2000).optional(),
  improvementAreas: z.array(z.string()).optional(),
  parentConsent: z.boolean().optional(),
  parentSignature: z.string().max(200).optional(),
});

type FeedbackFormValues = z.infer<typeof feedbackSchema>;

interface StudentFeedbackFormProps {
  token: string;
  sessionInfo: {
    tutor_name?: string;
    session_date?: string;
    subject?: string;
  };
  requiresParentConsent?: boolean;
  isUnder13?: boolean;
  onSuccess?: () => void;
}

export function StudentFeedbackForm({
  token,
  sessionInfo,
  requiresParentConsent = false,
  isUnder13 = false,
  onSuccess,
}: StudentFeedbackFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const form = useForm<FeedbackFormValues>({
    resolver: zodResolver(feedbackSchema),
    defaultValues: {
      sessionRating: 0,
      tutorHelpfulness: 0,
      contentClarity: 0,
      subjectKnowledge: 0,
      communication: 0,
      wouldRecommend: undefined,
      comments: "",
      improvementAreas: [],
      parentConsent: false,
      parentSignature: "",
    },
  });

  const onSubmit = async (data: FeedbackFormValues) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Validate parent consent for under-13 students
      if (requiresParentConsent && !data.parentConsent) {
        setSubmitError("Parent consent is required for students under 13");
        setIsSubmitting(false);
        return;
      }

      const response = await apiClient.submitFeedback({
        token,
        overall_rating: data.sessionRating,
        subject_knowledge_rating: data.subjectKnowledge,
        communication_rating: data.communication,
        patience_rating: data.tutorHelpfulness,
        engagement_rating: data.contentClarity,
        helpfulness_rating: data.tutorHelpfulness,
        would_recommend: data.wouldRecommend === "yes",
        improvement_areas: data.improvementAreas,
        free_text_feedback: data.comments,
        parent_consent_given: data.parentConsent || false,
        parent_signature: data.parentSignature,
      });

      if (response.success) {
        setSubmitSuccess(true);
        if (onSuccess) {
          onSuccess();
        }
      }
    } catch (error: any) {
      setSubmitError(
        error.response?.data?.detail || "Failed to submit feedback. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitSuccess) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <CheckCircle2 className="w-16 h-16 text-green-600 mx-auto" />
            <h2 className="text-2xl font-bold text-green-600">Thank You!</h2>
            <p className="text-gray-600">
              Your feedback has been submitted successfully. We appreciate you taking the time to
              help us improve.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Session Feedback</CardTitle>
        <CardDescription>
          {sessionInfo.tutor_name && `Tutor: ${sessionInfo.tutor_name}`}
          {sessionInfo.session_date && ` • ${sessionInfo.session_date}`}
          {sessionInfo.subject && ` • ${sessionInfo.subject}`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isUnder13 && (
          <Alert className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              This form is for students under 13. Parent or guardian consent is required to submit
              feedback. Please review our{" "}
              <a href="/privacy" className="underline font-medium">
                Privacy Policy
              </a>{" "}
              before submitting.
            </AlertDescription>
          </Alert>
        )}

        {submitError && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        )}

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Session Rating */}
            <FormField
              control={form.control}
              name="sessionRating"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base">Overall Session Rating</FormLabel>
                  <FormDescription>How would you rate this tutoring session?</FormDescription>
                  <FormControl>
                    <Rating
                      value={field.value}
                      onValueChange={field.onChange}
                      className="text-yellow-500"
                    >
                      {[...Array(5)].map((_, i) => (
                        <RatingButton key={i} size={32} />
                      ))}
                    </Rating>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Tutor Helpfulness */}
            <FormField
              control={form.control}
              name="tutorHelpfulness"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base">Tutor Helpfulness</FormLabel>
                  <FormDescription>How helpful was your tutor?</FormDescription>
                  <FormControl>
                    <Rating
                      value={field.value}
                      onValueChange={field.onChange}
                      className="text-yellow-500"
                    >
                      {[...Array(5)].map((_, i) => (
                        <RatingButton key={i} size={32} />
                      ))}
                    </Rating>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Content Clarity */}
            <FormField
              control={form.control}
              name="contentClarity"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base">Content Clarity</FormLabel>
                  <FormDescription>
                    How clear and easy to understand was the content?
                  </FormDescription>
                  <FormControl>
                    <Rating
                      value={field.value}
                      onValueChange={field.onChange}
                      className="text-yellow-500"
                    >
                      {[...Array(5)].map((_, i) => (
                        <RatingButton key={i} size={32} />
                      ))}
                    </Rating>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Subject Knowledge */}
            <FormField
              control={form.control}
              name="subjectKnowledge"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base">Subject Knowledge</FormLabel>
                  <FormDescription>How knowledgeable was your tutor about the subject?</FormDescription>
                  <FormControl>
                    <Rating
                      value={field.value}
                      onValueChange={field.onChange}
                      className="text-yellow-500"
                    >
                      {[...Array(5)].map((_, i) => (
                        <RatingButton key={i} size={32} />
                      ))}
                    </Rating>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Communication */}
            <FormField
              control={form.control}
              name="communication"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base">Communication</FormLabel>
                  <FormDescription>How well did your tutor communicate?</FormDescription>
                  <FormControl>
                    <Rating
                      value={field.value}
                      onValueChange={field.onChange}
                      className="text-yellow-500"
                    >
                      {[...Array(5)].map((_, i) => (
                        <RatingButton key={i} size={32} />
                      ))}
                    </Rating>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Would Recommend */}
            <FormField
              control={form.control}
              name="wouldRecommend"
              render={({ field }) => (
                <FormItem className="space-y-3">
                  <FormLabel className="text-base">Would you recommend this tutor?</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={field.onChange}
                      value={field.value}
                      className="flex gap-4"
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="yes" id="yes" />
                        <Label htmlFor="yes" className="cursor-pointer">
                          Yes
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="no" id="no" />
                        <Label htmlFor="no" className="cursor-pointer">
                          No
                        </Label>
                      </div>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Improvement Areas */}
            <FormField
              control={form.control}
              name="improvementAreas"
              render={() => (
                <FormItem>
                  <FormLabel className="text-base">Areas for Improvement (Optional)</FormLabel>
                  <FormDescription>Select any areas where the tutor could improve</FormDescription>
                  <div className="grid grid-cols-2 gap-3">
                    {IMPROVEMENT_AREAS.map((area) => (
                      <FormField
                        key={area.value}
                        control={form.control}
                        name="improvementAreas"
                        render={({ field }) => {
                          return (
                            <FormItem
                              key={area.value}
                              className="flex flex-row items-start space-x-3 space-y-0"
                            >
                              <FormControl>
                                <Checkbox
                                  checked={field.value?.includes(area.value)}
                                  onCheckedChange={(checked) => {
                                    return checked
                                      ? field.onChange([...(field.value || []), area.value])
                                      : field.onChange(
                                          field.value?.filter((value) => value !== area.value)
                                        );
                                  }}
                                />
                              </FormControl>
                              <FormLabel className="font-normal cursor-pointer">
                                {area.label}
                              </FormLabel>
                            </FormItem>
                          );
                        }}
                      />
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Comments */}
            <FormField
              control={form.control}
              name="comments"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base">Additional Comments (Optional)</FormLabel>
                  <FormDescription>
                    Share any additional feedback or suggestions
                  </FormDescription>
                  <FormControl>
                    <Textarea
                      placeholder="Your comments here..."
                      className="min-h-[100px] resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Parent Consent (for under-13) */}
            {requiresParentConsent && (
              <>
                <FormField
                  control={form.control}
                  name="parentConsent"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          required
                        />
                      </FormControl>
                      <div className="space-y-1 leading-none">
                        <FormLabel className="text-base">
                          Parent/Guardian Consent (Required)
                        </FormLabel>
                        <FormDescription>
                          I am the parent or legal guardian of this student and consent to the
                          collection and use of this feedback in accordance with the Privacy
                          Policy.
                        </FormDescription>
                      </div>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="parentSignature"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Parent/Guardian Name (Required)</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Full name"
                          {...field}
                          required={requiresParentConsent}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </>
            )}

            {/* Submit Button */}
            <Button type="submit" className="w-full" disabled={isSubmitting} size="lg">
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                "Submit Feedback"
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
