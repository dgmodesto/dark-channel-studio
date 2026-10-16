"use client";

import { useTranslations } from "next-intl";
import { useActionState } from "react";
import type { Template } from "@/lib/api";

export type FormState = { errorCode: string | null };

export function ChannelForm({
  templates,
  action,
}: {
  templates: Template[];
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
}) {
  const t = useTranslations("Channels");
  const te = useTranslations("Errors");
  const [state, formAction, pending] = useActionState(action, { errorCode: null });

  return (
    <form action={formAction} className="channel-form">
      <label>
        {t("name")}
        <input name="name" required maxLength={100} />
      </label>
      <label>
        {t("template")}
        <select name="template_id" required>
          {templates.map((tpl) => (
            <option key={tpl.id} value={tpl.id}>
              {tpl.name}
            </option>
          ))}
        </select>
      </label>
      <button type="submit" disabled={pending}>
        {t("create")}
      </button>
      {state.errorCode && (
        <p role="alert" data-status="unhealthy">
          {te.has(state.errorCode) ? te(state.errorCode as never) : te("unknown")}
        </p>
      )}
    </form>
  );
}
