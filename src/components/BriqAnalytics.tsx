"use client";

import { useEffect } from "react";
import { Analytics, type BeforeSendEvent } from "@vercel/analytics/next";

/** Set when the owner opens `/?briq-staff=<token>` once on that browser. */
const STORAGE_KEY = "briq-no-track";
const COOKIE = "briq-no-track=1";
const STAFF_TOKEN = "7f3c9a2e1b6d4c80";

function rememberStaffBrowser() {
  if (typeof window === "undefined") return;
  const token = new URLSearchParams(window.location.search).get("briq-staff");
  if (token !== STAFF_TOKEN) return;
  try {
    localStorage.setItem(STORAGE_KEY, "1");
  } catch {
    /* private mode */
  }
  document.cookie = `${COOKIE}; domain=.briq.kr; path=/; max-age=31536000; samesite=lax; secure`;
}

function isStaffBrowser() {
  try {
    if (localStorage.getItem(STORAGE_KEY) === "1") return true;
  } catch {
    /* ignore */
  }
  return document.cookie.split(";").some((part) => part.trim() === COOKIE);
}

/** Drops pageviews from the owner's browsers. Everyone else is counted. */
export function BriqAnalytics() {
  rememberStaffBrowser();
  useEffect(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.get("briq-staff") !== STAFF_TOKEN) return;
    url.searchParams.delete("briq-staff");
    const next = url.pathname + url.search + url.hash;
    window.history.replaceState(window.history.state, "", next);
  }, []);
  return (
    <Analytics
      beforeSend={(event: BeforeSendEvent) => (isStaffBrowser() ? null : event)}
    />
  );
}
