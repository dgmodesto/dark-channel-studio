import { setRequestLocale } from "next-intl/server";
import { LocaleSwitcher } from "@/components/LocaleSwitcher";
import { Shell } from "@/components/Shell";
import { StatusCard } from "@/components/StatusCard";

export const dynamic = "force-dynamic";

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <main>
      <LocaleSwitcher />
      <Shell />
      <StatusCard />
    </main>
  );
}
