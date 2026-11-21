import { Link } from "expo-router";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { products } from "../src/data/products";
import { useCart } from "../src/cart";

export default function HomeScreen() {
  const { count } = useCart();
  const featured = products.filter((p) => p.badge).slice(0, 4);

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <View style={styles.hero}>
        <Text style={styles.brand}>Briq</Text>
        <Text style={styles.headline}>British Boutique. Unique edit.</Text>
        <Text style={styles.support}>
          스포츠 · 패션의류 · 가방 · 악세서리. 영국 감성의 셀렉트 숍.
        </Text>
        <View style={styles.row}>
          <Link href="/shop" asChild>
            <Pressable style={styles.btnPrimary}>
              <Text style={styles.btnPrimaryText}>Shop now</Text>
            </Pressable>
          </Link>
          <Link href="/cart" asChild>
            <Pressable style={styles.btnGhost}>
              <Text style={styles.btnGhostText}>Cart ({count})</Text>
            </Pressable>
          </Link>
          <Link href="/account" asChild>
            <Pressable style={styles.btnGhost}>
              <Text style={styles.btnGhostText}>Account</Text>
            </Pressable>
          </Link>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Featured</Text>
      <View style={styles.grid}>
        {featured.map((p) => (
          <Link key={p.id} href={`/product/${p.id}`} asChild>
            <Pressable style={styles.card}>
              <View style={[styles.swatch, { backgroundColor: p.accent }]}>
                <Text style={styles.swatchText}>Briq</Text>
              </View>
              <Text style={styles.cardName}>{p.nameKo}</Text>
              <Text style={styles.cardMeta}>{p.badge}</Text>
            </Pressable>
          </Link>
        ))}
      </View>

      <View style={styles.pricing}>
        <Text style={styles.pricingMark}>TRANSPARENCY</Text>
        <Text style={styles.pricingTitle}>
          All-Inclusive Pricing,{"\n"}No Hidden Fees.
        </Text>
        <Text style={styles.pricingCopy}>
          Briq에서 안내하는 가격은 해외 항공 배송비와 관·부가세가{"\n"}모두
          포함된 최종 확정 금액입니다.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { paddingBottom: 40 },
  hero: {
    backgroundColor: "#0b1210",
    paddingHorizontal: 22,
    paddingTop: 28,
    paddingBottom: 32,
  },
  brand: {
    color: "#f7f8f5",
    fontSize: 64,
    fontWeight: "500",
    letterSpacing: 4,
  },
  headline: {
    color: "#f7f8f5",
    fontSize: 18,
    marginTop: 8,
    fontWeight: "500",
  },
  support: {
    color: "rgba(247,248,245,0.72)",
    marginTop: 10,
    lineHeight: 22,
  },
  row: { flexDirection: "row", gap: 10, marginTop: 22 },
  btnPrimary: {
    backgroundColor: "#f7f8f5",
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  btnPrimaryText: { color: "#0b1210", fontWeight: "600" },
  btnGhost: {
    borderWidth: 1,
    borderColor: "rgba(247,248,245,0.4)",
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  btnGhostText: { color: "#f7f8f5", fontWeight: "600" },
  sectionTitle: {
    fontSize: 24,
    fontWeight: "600",
    marginHorizontal: 18,
    marginTop: 24,
    marginBottom: 12,
  },
  grid: {
    paddingHorizontal: 14,
    flexDirection: "row",
    flexWrap: "wrap",
  },
  card: { width: "50%", padding: 6 },
  swatch: {
    aspectRatio: 4 / 5,
    justifyContent: "flex-end",
    padding: 12,
  },
  swatchText: { color: "#f7f8f5", letterSpacing: 2, fontWeight: "600" },
  cardName: { marginTop: 8, fontWeight: "600" },
  cardMeta: { color: "#5a655f", marginTop: 2, fontSize: 12 },
  pricing: {
    marginTop: 28,
    marginHorizontal: 18,
    paddingVertical: 34,
    paddingHorizontal: 22,
    backgroundColor: "#2c1e38",
    alignItems: "center",
  },
  pricingMark: {
    color: "#c9a8d8",
    fontSize: 11,
    letterSpacing: 4,
    fontWeight: "600",
  },
  pricingTitle: {
    color: "#f6f0f8",
    fontSize: 22,
    fontWeight: "600",
    textAlign: "center",
    marginTop: 12,
    lineHeight: 30,
  },
  pricingCopy: {
    color: "rgba(246,240,248,0.75)",
    textAlign: "center",
    marginTop: 12,
    lineHeight: 21,
    fontSize: 13,
  },
});
