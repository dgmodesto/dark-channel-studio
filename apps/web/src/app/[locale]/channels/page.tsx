import { getTranslations, setRequestLocale } from "next-intl/server";
import { ChannelForm } from "@/components/ChannelForm";
import { ChannelList } from "@/components/ChannelList";
import { LocaleSwitcher } from "@/components/LocaleSwitcher";
import { Link } from "@/i18n/navigation";
import { listChannels, listTemplates } from "@/lib/api";
import { createChannelAction, deleteChannelAction } from "./actions";

export const dynamic = "force-dynamic";

export default async function ChannelsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("Channels");
  const te = await getTranslations("Errors");
  const [channels, templates] = await Promise.all([listChannels(), listTemplates()]);

  return (
    <main>
      <LocaleSwitcher />
      <p>
        <Link href="/">{t("back")}</Link>
      </p>
      <h1>{t("title")}</h1>
      {!channels.ok || !templates.ok ? (
        <p role="alert" data-status="unreachable">
          {te("api.unreachable")}
        </p>
      ) : (
        <>
          <ChannelForm templates={templates.data} action={createChannelAction} />
          <ChannelList channels={channels.data} deleteAction={deleteChannelAction} />
        </>
      )}
    </main>
  );
}
