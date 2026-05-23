"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, Eye, EyeOff, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    setIsLoading(true);

    // Simulate authentication
    await new Promise((resolve) => setTimeout(resolve, 1200));

    if (email === "admin@meridiansolutions.ro" && password === "demo1234") {
      router.push("/dashboard");
    } else {
      setError("Invalid credentials. Use admin@meridiansolutions.ro / demo1234");
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-zinc-900 flex-col justify-between p-12">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600">
            <Building2 className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-semibold text-zinc-100">Business Control Hub</span>
        </div>

        <div className="space-y-6">
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400">
              AI-first ERP
            </p>
            <h1 className="text-4xl font-bold leading-tight text-zinc-100">
              Business intelligence for modern companies
            </h1>
            <p className="text-lg text-zinc-400">
              Full financial visibility, predictive cash flow, automated documents — all in one place.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4">
            {[
              { label: "Invoices processed", value: "12,400+" },
              { label: "Time saved / month", value: "38 hrs" },
              { label: "Companies active", value: "680+" },
              { label: "Avg. collection time", value: "−14 days" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg border border-zinc-800 bg-zinc-800/50 p-4">
                <p className="text-2xl font-bold text-zinc-100">{stat.value}</p>
                <p className="mt-1 text-sm text-zinc-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-sm text-zinc-600">
          © 2024 Meridian Solutions SRL. All rights reserved.
        </p>
      </div>

      {/* Right panel */}
      <div className="flex w-full lg:w-1/2 items-center justify-center bg-white px-8 py-12">
        <div className="w-full max-w-sm space-y-8">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600">
              <Building2 className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-zinc-900">Business Control Hub</span>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900">Welcome back</h2>
            <p className="text-sm text-zinc-500">
              Sign in to your account to continue
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@company.ro"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <button
                  type="button"
                  className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-md bg-red-50 border border-red-100 px-3 py-2.5">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>

          <div className="rounded-lg bg-zinc-50 border border-zinc-100 px-4 py-3">
            <p className="text-xs text-zinc-500 font-medium mb-1">Demo credentials</p>
            <p className="text-xs text-zinc-600">admin@meridiansolutions.ro</p>
            <p className="text-xs text-zinc-600">demo1234</p>
          </div>

          <p className="text-center text-xs text-zinc-400">
            By signing in, you agree to our{" "}
            <span className="text-indigo-600 hover:underline cursor-pointer">Terms of Service</span>{" "}
            and{" "}
            <span className="text-indigo-600 hover:underline cursor-pointer">Privacy Policy</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
