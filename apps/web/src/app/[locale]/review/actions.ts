"use server";

import { revalidatePath } from "next/cache";
import { decideReview } from "@/lib/api";

export type ReviewActionState = { error: boolean };

export async function decideReviewAction(
  _previous: ReviewActionState,
  formData: FormData,
): Promise<ReviewActionState> {
  const runId = String(formData.get("run_id") ?? "");
  const decision = String(formData.get("decision") ?? "");
  const notes = String(formData.get("notes") ?? "");
  if (!runId || !["approve", "request_changes"].includes(decision)) return { error: true };
  const result = await decideReview(runId, decision as "approve" | "request_changes", notes);
  if (!result.ok) return { error: true };
  revalidatePath("/[locale]/review", "page");
  return { error: false };
}
