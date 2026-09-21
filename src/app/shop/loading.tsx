export default function ShopLoading() {
  return (
    <div className="shop-loading" aria-busy="true" aria-label="쇼핑 목록 로딩">
      <div className="shop-loading__bar" />
      <div className="shop-loading__grid">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="shop-loading__card" />
        ))}
      </div>
    </div>
  );
}
