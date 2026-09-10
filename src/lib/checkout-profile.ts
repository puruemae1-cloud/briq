/**
 * Guest checkout profile (device-local).
 * After the first successful payment we remember PCCC + shipping defaults
 * so the next checkout can prefill without retyping.
 *
 * When membership ships, migrate this to an encrypted server-side
 * user profile and stop relying on localStorage alone.
 */

export const CHECKOUT_PROFILE_KEY = "briq-checkout-profile-v1";

export type CheckoutProfile = {
  name: string;
  /** Full phone e.g. 010-1234-5678 */
  phone: string;
  email?: string;
  /** Personal customs clearance code: P + 12 digits */
  customsCode: string;
  zonecode: string;
  addressBase: string;
  addressDetail: string;
  updatedAt: string;
};

const CUSTOMS_CODE_RE = /^P\d{12}$/;

export function normalizeCustomsCode(raw: string) {
  const cleaned = raw.replace(/\s+/g, "").toUpperCase();
  if (!cleaned) return "";
  return cleaned.startsWith("P") ? cleaned : `P${cleaned}`;
}

export function isValidCustomsCode(code: string) {
  return CUSTOMS_CODE_RE.test(normalizeCustomsCode(code));
}

export function loadCheckoutProfile(): CheckoutProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CHECKOUT_PROFILE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CheckoutProfile;
    if (!parsed?.customsCode || !isValidCustomsCode(parsed.customsCode)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveCheckoutProfile(
  profile: Omit<CheckoutProfile, "updatedAt">,
) {
  if (typeof window === "undefined") return;
  const code = normalizeCustomsCode(profile.customsCode);
  if (!isValidCustomsCode(code)) return;

  const next: CheckoutProfile = {
    ...profile,
    name: profile.name.trim(),
    customsCode: code,
    updatedAt: new Date().toISOString(),
  };

  try {
    window.localStorage.setItem(CHECKOUT_PROFILE_KEY, JSON.stringify(next));
  } catch {
    /* quota / private mode — ignore */
  }
}
