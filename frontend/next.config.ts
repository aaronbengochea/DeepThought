import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // @ts-expect-error -- reactCompiler is stable in Next.js 16 but types lag behind
  reactCompiler: true,
};

export default nextConfig;
