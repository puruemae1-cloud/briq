import { Link } from "expo-router";
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { formatKrw } from "../src/data/products";
import { useCart } from "../src/cart";

export default function CartScreen() {
  const { items, setQty, subtotal } = useCart();

  if (items.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.empty}>장바구니가 비어 있습니다.</Text>
        <Link href="/shop" asChild>
          <Pressable style={styles.btn}>
            <Text style={styles.btnText}>쇼핑하기</Text>
          </Pressable>
        </Link>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.page}>
      {items.map(({ product, variant, qty }) => {
        const unit = variant?.price ?? product.price;
        const label = variant
          ? `${product.nameKo} · ${variant.nameKo}`
          : product.nameKo;
        const thumb = variant?.image ?? product.image;
        const key = `${product.id}::${variant?.id ?? "default"}`;

        return (
          <View key={key} style={styles.row}>
            {thumb != null ? (
              <Image source={thumb} style={styles.thumb} />
            ) : (
              <View style={[styles.swatch, { backgroundColor: product.accent }]} />
            )}
            <View style={{ flex: 1 }}>
              <Text style={styles.name}>{label}</Text>
              <Text>{formatKrw(unit)}</Text>
              <View style={styles.qty}>
                <Pressable onPress={() => setQty(product.id, qty - 1, variant?.id)}>
                  <Text style={styles.qtyBtn}>−</Text>
                </Pressable>
                <Text>{qty}</Text>
                <Pressable onPress={() => setQty(product.id, qty + 1, variant?.id)}>
                  <Text style={styles.qtyBtn}>+</Text>
                </Pressable>
              </View>
            </View>
            <Text style={styles.line}>{formatKrw(unit * qty)}</Text>
          </View>
        );
      })}
      <View style={styles.footer}>
        <Text style={styles.total}>합계 {formatKrw(subtotal)}</Text>
        <Link href="/checkout" asChild>
          <Pressable style={styles.btn}>
            <Text style={styles.btnText}>결제하기</Text>
          </Pressable>
        </Link>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { padding: 16, gap: 14, paddingBottom: 40 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: 16 },
  empty: { color: "#5a655f" },
  row: {
    flexDirection: "row",
    gap: 12,
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.7)",
    padding: 12,
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.08)",
  },
  swatch: { width: 64, height: 80 },
  thumb: { width: 64, height: 80, backgroundColor: "#eee" },
  name: { fontWeight: "600", marginBottom: 4 },
  qty: { flexDirection: "row", alignItems: "center", gap: 12, marginTop: 8 },
  qtyBtn: { fontSize: 20, width: 24, textAlign: "center" },
  line: { fontWeight: "700" },
  footer: {
    marginTop: 8,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  total: { fontSize: 18, fontWeight: "700" },
  btn: { backgroundColor: "#1f4d3a", paddingHorizontal: 16, paddingVertical: 12 },
  btnText: { color: "#fff", fontWeight: "700" },
});
