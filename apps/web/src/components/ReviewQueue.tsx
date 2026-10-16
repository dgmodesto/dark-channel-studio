"use client";

import { useTranslations } from "next-intl";
import { useActionState } from "react";
import { useRef, useState } from "react";
import type { Review } from "@/lib/api";
import type { ReviewActionState } from "@/app/[locale]/review/actions";

function VideoPlayer({ runId, title }: { runId: string; title: string }) {
  const t = useTranslations("Review");
  const [failed, setFailed] = useState(false);
  return (
    <>
      <video
        controls
        preload="metadata"
        aria-label={t("videoLabel", { title })}
        onError={() => setFailed(true)}
      >
        <source src={`/api/reviews/${encodeURIComponent(runId)}/media/video`} type="video/mp4" />
        {t("mediaUnsupported")}
      </video>
      {failed && <p role="alert">{t("mediaError")}</p>}
    </>
  );
}

function AudioPlayer({ runId, index }: { runId: string; index: number }) {
  const t = useTranslations("Review");
  const [failed, setFailed] = useState(false);
  return (
    <div className="review-audio">
      <p id={`audio-label-${runId}-${index}`}>{t("audioLabel", { number: index + 1 })}</p>
      <audio
        aria-labelledby={`audio-label-${runId}-${index}`}
        controls
        preload="none"
        src={`/api/reviews/${encodeURIComponent(runId)}/media/audio/${index}`}
        onError={() => setFailed(true)}
      >
        {t("mediaUnsupported")}
      </audio>
      {failed && <p role="alert">{t("mediaError")}</p>}
    </div>
  );
}

function ReviewDecisionForm({
  runId,
  action,
}: {
  runId: string;
  action: (prev: ReviewActionState, formData: FormData) => Promise<ReviewActionState>;
}) {
  const t = useTranslations("Review");
  const [state, formAction, pending] = useActionState(action, { error: false });
  const [notesMissing, setNotesMissing] = useState(false);
  const notesRef = useRef<HTMLTextAreaElement>(null);
  return (
    <form
      action={formAction}
      className="review-decision"
      onSubmit={(event) => {
        const submitter = event.nativeEvent.submitter;
        const notes = notesRef.current?.value.trim();
        if (submitter instanceof HTMLButtonElement && submitter.value === "request_changes" && !notes) {
          event.preventDefault();
          setNotesMissing(true);
          notesRef.current?.focus();
        }
      }}
    >
      <input type="hidden" name="run_id" value={runId} />
      <label>
        {t("notesLabel")}
        <textarea
          name="notes"
          rows={3}
          maxLength={4000}
          ref={notesRef}
          aria-invalid={notesMissing}
          aria-describedby={notesMissing ? `notes-error-${runId}` : undefined}
          onChange={() => setNotesMissing(false)}
        />
      </label>
      {notesMissing && (
        <p role="alert" id={`notes-error-${runId}`}>
          {t("notesRequired")}
        </p>
      )}
      <div className="review-actions">
        <button name="decision" value="approve" disabled={pending} type="submit">
          {pending ? t("saving") : t("approve")}
        </button>
        <button
          name="decision"
          value="request_changes"
          disabled={pending}
          type="submit"
          formNoValidate
        >
          {pending ? t("saving") : t("requestChanges")}
        </button>
      </div>
      {state.error && <p role="alert">{t("decisionError")}</p>}
    </form>
  );
}

export function ReviewQueue({
  reviews,
  action,
}: {
  reviews: Review[];
  action: (prev: ReviewActionState, formData: FormData) => Promise<ReviewActionState>;
}) {
  const t = useTranslations("Review");
  if (reviews.length === 0) return <p className="review-empty">{t("empty")}</p>;
  return (
    <section aria-label={t("listLabel")} className="review-queue">
      {reviews.map((review) => (
        <article className="review-card" key={review.run_id}>
          <header>
            <div>
              <h2>{review.title}</h2>
              <p>{t("runId", { runId: review.run_id })}</p>
            </div>
            <span className="review-status" data-status={review.status}>
              {t(`status.${review.status}`)}
            </span>
          </header>
          <VideoPlayer runId={review.run_id} title={review.title} />
          {review.audio_urls.map((_, index) => (
            <AudioPlayer key={`${review.run_id}-${index}`} runId={review.run_id} index={index} />
          ))}
          {review.status === "awaiting_review" ? (
            <ReviewDecisionForm runId={review.run_id} action={action} />
          ) : (
            <p className="review-notes">
              {review.status === "approved" ? t("approvedNotice") : t("changesNotice")}
              {review.notes ? ` ${review.notes}` : ""}
            </p>
          )}
        </article>
      ))}
    </section>
  );
}
