import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Spendly",
  description: "A clear foundation for thoughtful financial decisions.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
