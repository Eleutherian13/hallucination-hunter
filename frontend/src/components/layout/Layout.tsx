"use client";

import { ReactNode } from "react";
import Head from "next/head";
import Sidebar from "./Sidebar";
import Header from "./Header";

interface LayoutProps {
  children: ReactNode;
  title: string;
  description?: string;
  pageTitle?: string;
}

export default function Layout({
  children,
  title,
  description,
  pageTitle,
}: LayoutProps) {
  const fullTitle = pageTitle
    ? `${pageTitle} | Hallucination Hunter v2.0`
    : "Hallucination Hunter v2.0 - AI Fact-Checking System";

  return (
    <>
      <Head>
        <title>{fullTitle}</title>
        <meta
          name="description"
          content={
            description || "AI-Powered Fact-Checking System for LLM Outputs"
          }
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-dark-bg">
        <Sidebar />

        <main className="ml-64">
          <Header title={title} description={description} />

          <div className="p-8">{children}</div>
        </main>
      </div>
    </>
  );
}
