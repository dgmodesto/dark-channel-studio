import { getTranslations, setRequestLocale } from "next-intl/server";
import { LocaleSwitcher } from "@/components/LocaleSwitcher";
import { ReviewQueue } from "@/components/ReviewQueue";
import { Link } from "@/i18n/navigation";
import { listReviews } from "@/lib/api";
import { decideReviewAction } from "./actions";

export const dynamic = "force-dynamic";

export default async function ReviewPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("Review");
  const te = await getTranslations("Errors");
  const reviews = await listReviews();

  return (
    <main>
      <LocaleSwitcher />
      <p>
        <Link href="/">{t("back")}</Link>
      </p>
      <h1>{t("title")}</h1>
      {!reviews.ok ? (
        <p role="alert" data-status="unreachable">
          {te("api.unreachable")}
        </p>
      ) : (
        <ReviewQueue reviews={reviews.data} action={decideReviewAction} />
      )}
    </main>
  );
}
