export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diff = (Date.now() - then) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.round(diff / 60)} min ago`;
  if (diff < 86_400) return `${Math.round(diff / 3600)} hr ago`;
  if (diff < 604_800) return `${Math.round(diff / 86_400)} d ago`;
  return new Date(iso).toLocaleDateString();
}
