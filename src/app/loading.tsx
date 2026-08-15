export default function Loading() {
  return (
    <div
      className="route-loading"
      aria-hidden="true"
      // Keeps layout height while the next route streams in.
      data-route-loading=""
    />
  );
}
