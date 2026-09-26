import { BannerImage } from "@/components/BannerImage";
import { CollectionBestsellerTier } from "@/components/CollectionReveal";
import { CollectionTierBlock } from "@/components/CollectionTierBlock";
import { ShopFastLink } from "@/components/ShopFastLink";
import { bannerFocalForSrc } from "@/lib/banner-focal";
import { getHomepageData } from "@/lib/homepage-feed";

/** Locked Gucci Primavera hero — not rotated weekly. */
const COLLECTION_100_BANNER = "/banners/collection-100-gucci.jpg";

export async function Collection100() {
  // Server-side: 신상품 / 하이엔드 always reflect newest registeredAt in HTML.
  const { signature, newItems } = await getHomepageData();

  return (
    <section className="collection-100" id="collection-100" aria-label="Briq 100 컬렉션">
      <div className="collection-100__banner">
        <BannerImage
          className="collection-100__banner-img"
          src={COLLECTION_100_BANNER}
          alt=""
          aria-hidden
          loading="lazy"
          style={{
            objectPosition: bannerFocalForSrc(COLLECTION_100_BANNER, "center 40%"),
          }}
        />
        <div className="collection-100__banner-shade" aria-hidden />
        <div className="collection-100__banner-content">
          <p className="collection-100__eyebrow">Briq Edit</p>
          <h2 className="collection-100__title">
            가장 사랑받는 베스트셀러부터
            <br className="br-mobile" /> 플래그십 모델까지
          </h2>
        </div>
      </div>

      <div className="section collection-100__body">
        <CollectionTierBlock tier="signature" products={signature} />
        <CollectionBestsellerTier />
        <CollectionTierBlock tier="new" products={newItems} />

        <div className="collection-100__sentinel">
          <ShopFastLink
            href="/shop?sort=new"
            className="btn btn-solid collection-100__more-btn"
          >
            신상 보러가기
          </ShopFastLink>
        </div>
      </div>
    </section>
  );
}
