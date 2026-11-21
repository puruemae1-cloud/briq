export function HomeScreenHint() {
  return (
    <section className="card p-5">
      <p className="text-[0.72rem] tracking-[0.18em] uppercase text-[var(--muted)]">
        Home screen
      </p>
      <h2 className="display mt-1 text-2xl">홈 화면에 배대지 두기</h2>
      <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
        아이폰 Safari에서 이 사이트를 연 다음 <strong>공유 → 홈 화면에 추가</strong>를
        하면, ASOS와 배대지를 앱처럼 오갈 수 있습니다. 상품 주소를 복사하고 홈 화면의
        배대지를 누르면 붙여넣기 칸이 바로 있습니다.
      </p>
    </section>
  );
}
