import { Link } from "expo-router";
import { useMemo, useState } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { categories, formatKrw, products } from "../src/data/products";

export default function ShopScreen() {
  const [category, setCategory] = useState<string>("all");
  const list = useMemo(
    () =>
      category === "all"
        ? products
        : products.filter((p) => p.category === category),
    [category],
  );

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chips}
      >
        {categories.map((c) => (
          <Pressable
            key={c.id}
            onPress={() => setCategory(c.id)}
            style={[styles.chip, category === c.id && styles.chipActive]}
          >
            <Text
              style={[
                styles.chipText,
                category === c.id && styles.chipTextActive,
              ]}
            >
              {c.labelKo}
            </Text>
          </Pressable>
        ))}
      </ScrollView>

      <View style={styles.grid}>
        {list.map((p) => (
          <Link key={p.id} href={`/product/${p.id}`} asChild>
            <Pressable style={styles.card}>
              <View style={[styles.swatch, { backgroundColor: p.accent }]} />
              <Text style={styles.brand}>{p.brand}</Text>
              <Text style={styles.name}>{p.nameKo}</Text>
              <Text style={styles.price}>{formatKrw(p.price)}</Text>
            </Pressable>
          </Link>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { paddingBottom: 40 },
  chips: { paddingHorizontal: 14, paddingVertical: 14, gap: 8 },
  chip: {
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.15)",
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginRight: 8,
    backgroundColor: "rgba(255,255,255,0.7)",
  },
  chipActive: { backgroundColor: "#0b1210", borderColor: "#0b1210" },
  chipText: { color: "#0b1210" },
  chipTextActive: { color: "#f7f8f5" },
  grid: { flexDirection: "row", flexWrap: "wrap", paddingHorizontal: 10 },
  card: { width: "50%", padding: 8 },
  swatch: { aspectRatio: 4 / 5 },
  brand: {
    marginTop: 8,
    fontSize: 11,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: "#6a736c",
  },
  name: { marginTop: 2, fontWeight: "600" },
  price: { marginTop: 4, fontWeight: "700" },
});
