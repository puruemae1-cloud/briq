/** Lightweight demo hash shared by the client login and the Q&A staff check. */
export function hashPassword(password: string) {
  let h = 2166136261;
  for (let i = 0; i < password.length; i++) {
    h ^= password.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return `demo_${(h >>> 0).toString(16)}`;
}
