"use server";

import { revalidatePath } from "next/cache";
import type { FormState } from "@/components/ChannelForm";
import { createChannel, deleteChannel } from "@/lib/api";

export async function createChannelAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const name = String(formData.get("name") ?? "").trim();
  const templateId = String(formData.get("template_id") ?? "");
  const result = await createChannel(name, templateId);
  if (!result.ok) return { errorCode: result.code };
  revalidatePath("/[locale]/channels", "page");
  return { errorCode: null };
}

export async function deleteChannelAction(formData: FormData): Promise<void> {
  await deleteChannel(String(formData.get("id") ?? ""));
  revalidatePath("/[locale]/channels", "page");
}
