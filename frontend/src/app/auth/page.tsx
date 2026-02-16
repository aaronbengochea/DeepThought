"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { SignInForm } from "@/components/auth/sign-in-form";
import { SignUpForm } from "@/components/auth/sign-up-form";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export default function AuthPage() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden px-4">
      {/* ── Aurora background ── */}
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        {/* Base gradient */}
        <div className="absolute inset-0 bg-[var(--gradient-surface)]" />

        {/* Floating blobs */}
        <div
          className="aurora-blob absolute -left-32 -top-32 h-[500px] w-[500px] bg-sky-500/20"
          style={{ animationDelay: "0s" }}
        />
        <div
          className="aurora-blob absolute -right-24 top-1/4 h-[400px] w-[400px] bg-violet-500/15"
          style={{ animationDelay: "2s" }}
        />
        <div
          className="aurora-blob absolute -bottom-20 left-1/3 h-[450px] w-[450px] bg-fuchsia-500/10"
          style={{ animationDelay: "4s" }}
        />

        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(var(--text-muted) 1px, transparent 1px), linear-gradient(90deg, var(--text-muted) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      {/* ── Theme toggle ── */}
      <div className="absolute right-6 top-6 z-10">
        <ThemeToggle />
      </div>

      {/* ── Auth card ── */}
      <div className="relative z-10 w-full max-w-[420px]">
        {/* Logo */}
        <div className="mb-8 text-center">
          <h1 className="font-[family-name:var(--font-display)] text-4xl font-bold tracking-tight">
            <span className="gradient-text">Operate</span>
            <span className="text-accent">+</span>
          </h1>
          <p className="mt-2 text-sm text-text-secondary">
            AI-powered multi-agent calculations
          </p>
        </div>

        {/* Card */}
        <div className="gradient-border rounded-2xl border border-border-subtle bg-surface-elevated/80 p-8 backdrop-blur-xl">
          {/* Tab toggle */}
          <div className="mb-6 flex rounded-xl bg-surface p-1">
            <button
              onClick={() => setMode("signin")}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-all duration-200
                ${
                  mode === "signin"
                    ? "bg-surface-elevated text-text-primary shadow-sm"
                    : "text-text-muted hover:text-text-secondary"
                }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setMode("signup")}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-all duration-200
                ${
                  mode === "signup"
                    ? "bg-surface-elevated text-text-primary shadow-sm"
                    : "text-text-muted hover:text-text-secondary"
                }`}
            >
              Sign Up
            </button>
          </div>

          {/* Form */}
          {mode === "signin" ? <SignInForm /> : <SignUpForm />}
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-xs text-text-muted">
          {mode === "signin" ? (
            <>
              Don&apos;t have an account?{" "}
              <button
                onClick={() => setMode("signup")}
                className="text-accent hover:text-accent-hover transition-colors"
              >
                Create one
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={() => setMode("signin")}
                className="text-accent hover:text-accent-hover transition-colors"
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
