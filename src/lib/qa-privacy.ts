/** Hide the front half of a mailbox id. The domain stays visible. */
export function maskInquiryEmail(email: string): string {
  const trimmed = email.trim();
  const at = trimmed.lastIndexOf("@");
  const local = at > 0 ? trimmed.slice(0, at) : trimmed;
  const domain = at > 0 ? trimmed.slice(at) : "";
  if (!local) return domain || trimmed;
  const hidden = Math.ceil(local.length / 2);
  return `${"*".repeat(hidden)}${local.slice(hidden)}${domain}`;
}
