import { BannerImage } from "@/components/BannerImage";
import { pickRotating } from "@/data/home-banners";
import { getCollection100 } from "@/data/products";
import { CollectionReveal } from "@/components/CollectionReveal";

const collectionBannerImages = [
  "/banners/rot-luxury-1.jpg",
  "/banners/rot-event-1.jpg",
  "/banners/rot-cloth-1.jpg",
  "/banners/rot-hero-2.jpg",
  "/banners/rot-luxury-2.jpg",
  "/banners/rot-event-2.jpg",
];

export function Collection100() {
  const banner = pickRotating(collectionBannerImages, 3);
  const list = getCollection100();

  return (
    <section className="collection-100" id="collection-100" aria-label="Briq 100 컬렉션">
      <div className="collection-100__banner">
        <BannerImage
          className="collection-100__banner-img"
          src={banner}
          alt=""
          aria-hidden
          loading="lazy"
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
        <CollectionReveal products={list} />
      </div>
    </section>
  );
}
