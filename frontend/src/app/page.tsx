type ApiHealth = "available" | "unavailable";

async function checkApiHealth(): Promise<ApiHealth> {
  const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

  try {
    const response = await fetch(`${backendUrl}/health/live`, { cache: "no-store" });
    return response.ok ? "available" : "unavailable";
  } catch {
    return "unavailable";
  }
}

export const dynamic = "force-dynamic";

export default async function Home() {
  const apiHealth = await checkApiHealth();

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-16">
      <p className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-emerald-800">
        Spendly · Foundation
      </p>
      <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
        A clearer view of your financial decisions.
      </h1>
      <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
        The application foundation is running. Core financial features will be added in reviewed milestones.
      </p>
      <section aria-live="polite" className="mt-10 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-medium">Backend connection</h2>
        <p className="mt-2 text-sm text-slate-600">
          <span
            aria-label={apiHealth === "available" ? "Backend available" : "Backend unavailable"}
            className={`mr-2 inline-block h-2.5 w-2.5 rounded-full ${apiHealth === "available" ? "bg-emerald-600" : "bg-slate-400"}`}
          />
          {apiHealth === "available" ? "API is responding." : "API is unavailable. Start the backend to connect."}
        </p>
      </section>
    </main>
  );
}
