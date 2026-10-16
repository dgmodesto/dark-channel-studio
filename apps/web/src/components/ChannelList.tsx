import { useTranslations } from "next-intl";
import type { Channel } from "@/lib/api";

export function ChannelList({
  channels,
  deleteAction,
}: {
  channels: Channel[];
  deleteAction: (formData: FormData) => void | Promise<void>;
}) {
  const t = useTranslations("Channels");
  if (channels.length === 0) return <p>{t("empty")}</p>;
  return (
    <ul className="channel-list" aria-label={t("listLabel")}>
      {channels.map((c) => (
        <li key={c.id}>
          <strong>{c.name}</strong>
          <span>
            {" "}
            {t("templateInfo", { template: c.template_id, version: c.template_version })}
          </span>
          <form action={deleteAction}>
            <input type="hidden" name="id" value={c.id} />
            <button type="submit">{t("delete")}</button>
          </form>
        </li>
      ))}
    </ul>
  );
}
