"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getUserId } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (pathname === "/signin") {
      setReady(true);
      return;
    }
    const id = getUserId();
    if (!id) {
      router.replace("/signin");
    } else {
      setReady(true);
    }
  }, [pathname, router]);

  if (!ready) return null;
  return <>{children}</>;
}
