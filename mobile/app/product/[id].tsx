import { Link, useLocalSearchParams } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import {
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { formatKrw, getProduct, type ProductVariant } from "../../src/data/products";
import { useCart } from "../../src/cart";

export default function ProductScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const product = getProduct(String(id));
  const { add } = useCart();

  const variants = useMemo(
    () => (product?.variants ?? []).filter((v) => v.inStock),
    [product],
  );
  const [variantId, setVariantId] = useState<string | undefined>(undefined);
  const [activeImage, setActiveImage] = useState(0);

  useEffect(() => {
    setVariantId(variants[0]?.id);
  }, [product?.id, variants]);

  useEffect(() => {
    setActiveImage(0);
  }, [variantId, product?.id]);

  if (!product) {
    return (
      <View style={styles.center}>
        <Text>상품을 찾을 수 없습니다.</Text>
      </View>
    );
  }

  const selected: ProductVariant | undefined =
    variants.find((v) => v.id === variantId) ?? variants[0];
  const unitPrice = selected?.price ?? product.price;
  const gallery =
    (selected?.images && selected.images.length > 0
      ? selected.images
      : selected?.image
        ? [selected.image, ...(product.images ?? []).filter((i) => i !== selected.image)]
        : product.images?.length
          ? product.images
          : [product.image]
    ).filter(Boolean);
  const mainImage = gallery[Math.min(activeImage, gallery.length - 1)] ?? product.image;

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <View style={[styles.media, { backgroundColor: product.accent }]}>
        {mainImage != null ? (
          <Pressable
            onPress={() =>
              gallery.length > 1 &&
              setActiveImage((i) => (i + 1) % gallery.length)
            }
            style={StyleSheet.absoluteFill}
          >
            <Image
              key={`${selected?.id ?? product.id}-${activeImage}`}
              source={mainImage}
              style={styles.mediaImage}
              resizeMode="contain"
            />
          </Pressable>
        ) : (
          <Text style={styles.mediaBrand}>Briq</Text>
        )}
        {gallery.length > 1 ? (
          <Text style={styles.mediaCount}>
            {Math.min(activeImage, gallery.length - 1) + 1} / {gallery.length}
          </Text>
        ) : null}
      </View>

      {gallery.length > 1 ? (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.thumbs}
        >
          {gallery.map((img, i) => (
            <Pressable
              key={`${img}-${i}`}
              onPress={() => setActiveImage(i)}
              style={[styles.thumb, i === activeImage && styles.thumbActive]}
            >
              <Image source={img} style={styles.thumbImage} resizeMode="contain" />
            </Pressable>
          ))}
        </ScrollView>
      ) : null}

      <View style={styles.body}>
        <Text style={styles.brand}>{product.brand}</Text>
        <Text style={styles.name}>{product.nameKo}</Text>
        <Text style={styles.price}>{formatKrw(unitPrice)}</Text>

        {variants.length > 0 ? (
          <View style={styles.variantBlock}>
            <Text style={styles.variantLabel}>
              {product.brand === "Christopher Ward" ? "스트랩 · " : "컬러 · "}
              <Text style={styles.variantStrong}>{selected?.nameKo}</Text>
            </Text>
            <View style={styles.variantGrid}>
              {variants.map((v) => {
                const active = v.id === selected?.id;
                return (
                  <Pressable
                    key={v.id}
                    onPress={() => setVariantId(v.id)}
                    style={[styles.swatch, active && styles.swatchActive]}
                  >
                    <Image source={v.image} style={styles.swatchImage} />
                    <Text style={styles.swatchText} numberOfLines={2}>
                      {v.nameKo}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        ) : null}

        {product.descriptionKo ? (
          <Text style={styles.desc}>{product.descriptionKo}</Text>
        ) : null}

        {product.featuresKo?.length ? (
          <View style={styles.techBlock}>
            <Text style={styles.techTitle}>특징</Text>
            {product.featuresKo.map((f) => (
              <Text key={f} style={styles.techItem}>
                · {f}
              </Text>
            ))}
          </View>
        ) : null}

        {product.techSpecs?.length ? (
          <View style={styles.techBlock}>
            <Text style={styles.techTitle}>기술 사양</Text>
            {product.techSpecs.map((s) => (
              <View key={`${s.labelKo}-${s.valueKo}`} style={styles.specRow}>
                <Text style={styles.specLabel}>{s.labelKo}</Text>
                <Text style={styles.specValue}>{s.valueKo}</Text>
              </View>
            ))}
          </View>
        ) : null}

        <Pressable style={styles.btn} onPress={() => add(product, selected)}>
          <Text style={styles.btnText}>장바구니 담기</Text>
        </Pressable>
        <Link href="/cart" asChild>
          <Pressable style={styles.btnOutline}>
            <Text style={styles.btnOutlineText}>장바구니 보기</Text>
          </Pressable>
        </Link>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  page: { paddingBottom: 40 },
  media: {
    aspectRatio: 4 / 5,
    justifyContent: "flex-end",
    overflow: "hidden",
    backgroundColor: "#f4f4f2",
  },
  mediaImage: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    width: "100%",
    height: "100%",
  },
  mediaBrand: {
    position: "absolute",
    left: 16,
    bottom: 16,
    fontSize: 28,
    fontWeight: "700",
  },
  mediaCount: {
    position: "absolute",
    right: 12,
    bottom: 12,
    backgroundColor: "rgba(255,255,255,0.88)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    fontSize: 11,
    fontWeight: "600",
    overflow: "hidden",
  },
  thumbs: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  thumb: {
    width: 64,
    height: 80,
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.12)",
    marginRight: 8,
    backgroundColor: "#fff",
    padding: 2,
  },
  thumbActive: { borderColor: "rgba(11,18,16,0.55)" },
  thumbImage: { width: "100%", height: "100%" },
  body: { padding: 16, gap: 10 },
  brand: { fontSize: 12, letterSpacing: 1, color: "#666", textTransform: "uppercase" },
  name: { fontSize: 22, fontWeight: "700", color: "#0b1210" },
  price: { fontSize: 18, fontWeight: "650", marginBottom: 4 },
  variantBlock: { marginTop: 8, gap: 8 },
  variantLabel: { fontSize: 14, color: "#444" },
  variantStrong: { fontWeight: "700", color: "#0b1210" },
  variantGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  swatch: {
    width: "47%",
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.12)",
    padding: 8,
    gap: 6,
  },
  swatchActive: { borderColor: "rgba(11,18,16,0.55)" },
  swatchImage: { width: "100%", aspectRatio: 4 / 5, backgroundColor: "#f4f4f2" },
  swatchText: { fontSize: 12, color: "#222" },
  desc: { marginTop: 8, fontSize: 14, lineHeight: 21, color: "#333" },
  techBlock: { marginTop: 12, gap: 6 },
  techTitle: { fontSize: 16, fontWeight: "700", marginBottom: 4 },
  techItem: { fontSize: 13, lineHeight: 19, color: "#333" },
  specRow: {
    flexDirection: "row",
    gap: 10,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "rgba(11,18,16,0.12)",
  },
  specLabel: { width: 110, fontSize: 11, color: "#777", textTransform: "uppercase" },
  specValue: { flex: 1, fontSize: 13, color: "#222", fontWeight: "560" },
  btn: {
    marginTop: 16,
    backgroundColor: "#0b1210",
    paddingVertical: 14,
    alignItems: "center",
  },
  btnText: { color: "#fff", fontWeight: "700" },
  btnOutline: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: "#0b1210",
    paddingVertical: 14,
    alignItems: "center",
  },
  btnOutlineText: { color: "#0b1210", fontWeight: "700" },
});
