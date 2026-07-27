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

  useEffect(() => {
    setVariantId(variants[0]?.id);
  }, [product?.id, variants]);

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
  const mainImage = selected?.image ?? product.image;

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <View style={[styles.media, { backgroundColor: product.accent }]}>
        {mainImage != null ? (
          <Image
            key={selected?.id ?? product.id}
            source={mainImage}
            style={styles.mediaImage}
            resizeMode="cover"
          />
        ) : (
          <Text style={styles.mediaBrand}>Briq</Text>
        )}
      </View>

      <View style={styles.body}>
        <Text style={styles.brand}>{product.brand}</Text>
        <Text style={styles.name}>{product.nameKo}</Text>
        <Text style={styles.price}>{formatKrw(unitPrice)}</Text>

        {variants.length > 0 ? (
          <View style={styles.variantBlock}>
            <Text style={styles.variantLabel}>
              컬러 · <Text style={styles.variantStrong}>{selected?.nameKo}</Text>
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
    color: "#f7f8f5",
    fontSize: 42,
    letterSpacing: 4,
    fontWeight: "500",
    padding: 20,
  },
  body: { padding: 20 },
  brand: {
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: "#6a736c",
    fontSize: 12,
  },
  name: { fontSize: 28, fontWeight: "600", marginTop: 6 },
  price: { fontSize: 20, fontWeight: "700", marginVertical: 14 },
  desc: { lineHeight: 22, color: "#2a332e", marginTop: 8 },
  variantBlock: { marginBottom: 8 },
  variantLabel: { fontSize: 15, marginBottom: 10, color: "#2a332e" },
  variantStrong: { fontWeight: "700" },
  variantGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  swatch: {
    width: "31%",
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.12)",
    backgroundColor: "#fff",
    padding: 6,
  },
  swatchActive: {
    borderColor: "#1f4d3a",
    borderWidth: 2,
  },
  swatchImage: {
    width: "100%",
    aspectRatio: 1,
    backgroundColor: "#eee",
  },
  swatchText: {
    marginTop: 6,
    fontSize: 11,
    lineHeight: 14,
    color: "#3a433d",
  },
  btn: {
    marginTop: 20,
    backgroundColor: "#1f4d3a",
    paddingVertical: 14,
    alignItems: "center",
  },
  btnText: { color: "#fff", fontWeight: "700" },
  btnOutline: {
    marginTop: 10,
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.15)",
    paddingVertical: 14,
    alignItems: "center",
  },
  btnOutlineText: { fontWeight: "600" },
});
