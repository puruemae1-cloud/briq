import AsyncStorage from "@react-native-async-storage/async-storage";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useMobileAuth } from "../src/auth";
import { useMobileOrders } from "../src/orders";
import { formatKrw } from "../src/data/products";
import { useCart } from "../src/cart";

const PROFILE_KEY = "briq-checkout-profile-v1";
const CUSTOMS_RE = /^P\d{12}$/;

const methods = [
  { id: "naverpay", label: "네이버페이" },
  { id: "kakaopay", label: "카카오페이" },
  { id: "tosspay", label: "토스페이" },
  { id: "card", label: "신용/체크카드" },
] as const;

type SavedProfile = {
  name: string;
  phone: string;
  address: string;
  customsCode: string;
};

function normalizeCustomsCode(raw: string) {
  const cleaned = raw.replace(/\s+/g, "").toUpperCase();
  if (!cleaned) return "";
  return cleaned.startsWith("P") ? cleaned : `P${cleaned}`;
}

export default function CheckoutScreen() {
  const { items, subtotal, clear } = useCart();
  const { currentUser, updateProfile } = useMobileAuth();
  const { addOrder } = useMobileOrders(currentUser?.id);
  const [method, setMethod] = useState<(typeof methods)[number]["id"]>("naverpay");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [customsCode, setCustomsCode] = useState("P");
  const [profileHint, setProfileHint] = useState("");

  useEffect(() => {
    const fromUser = currentUser?.profile;
    if (fromUser) {
      setName(fromUser.name);
      setPhone(fromUser.phone);
      setAddress(fromUser.address);
      setCustomsCode(fromUser.customsCode);
      setProfileHint("회원 정보가 자동으로 불러와졌습니다.");
      return;
    }

    AsyncStorage.getItem(PROFILE_KEY)
      .then((raw) => {
        if (!raw) {
          if (currentUser) {
            setName(currentUser.name);
            setPhone(currentUser.phone ?? "");
          }
          return;
        }
        const saved = JSON.parse(raw) as SavedProfile;
        if (!saved?.customsCode || !CUSTOMS_RE.test(saved.customsCode)) return;
        setName(saved.name ?? "");
        setPhone(saved.phone ?? "");
        setAddress(saved.address ?? "");
        setCustomsCode(saved.customsCode);
        setProfileHint("이전 결제 정보가 자동으로 불러와졌습니다.");
      })
      .catch(() => {});
  }, [currentUser]);

  if (items.length === 0) {
    return (
      <View style={styles.center}>
        <Text>결제할 상품이 없습니다.</Text>
      </View>
    );
  }

  async function pay() {
    const code = normalizeCustomsCode(customsCode);
    if (!name || !phone || !address) {
      Alert.alert("입력 확인", "이름, 휴대폰, 배송지를 입력해 주세요.");
      return;
    }
    if (!CUSTOMS_RE.test(code)) {
      Alert.alert(
        "개인통관부호",
        "P로 시작하는 13자리 개인통관부호를 입력해 주세요.",
      );
      return;
    }

    await new Promise((r) => setTimeout(r, 500));

    const profile = {
      name: name.trim(),
      phone: phone.trim(),
      address: address.trim(),
      customsCode: code,
    };
    await AsyncStorage.setItem(PROFILE_KEY, JSON.stringify(profile));

    if (currentUser) {
      await updateProfile(profile);
      const orderId = `BRIQ-${Date.now().toString(36).toUpperCase()}`;
      await addOrder({
        id: orderId,
        userId: currentUser.id,
        paymentId: `DEMO-${orderId}`,
        paymentMethod: methods.find((m) => m.id === method)?.label ?? method,
        status: "paid",
        totalKrw: subtotal,
        customsCode: code,
        customerName: profile.name,
        customerPhone: profile.phone,
        address: profile.address,
        lines: items.map((i) => ({
          nameKo: i.variant
            ? `${i.product.nameKo} · ${i.variant.nameKo}`
            : i.product.nameKo,
          qty: i.qty,
          unitPrice: i.variant?.price ?? i.product.price,
        })),
        createdAt: new Date().toISOString(),
      });
    }

    clear();
    Alert.alert(
      "주문 접수",
      currentUser
        ? `결제가 완료되었습니다.\n마이페이지에서 주문·결제이력을 확인할 수 있습니다.`
        : `데모 결제 완료\n개인통관부호가 저장되었습니다.\n로그인하면 주문 이력이 보관됩니다.`,
      [
        {
          text: "확인",
          onPress: () => router.replace(currentUser ? "/account" : "/"),
        },
      ],
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <View style={styles.notice}>
        <Text style={styles.noticeText}>
          {currentUser
            ? `${currentUser.name} 님으로 결제 중입니다.`
            : "비회원 결제입니다. 로그인하면 주문 이력이 저장됩니다."}
        </Text>
      </View>

      {profileHint ? <Text style={styles.hintBanner}>{profileHint}</Text> : null}

      <Text style={styles.label}>이름</Text>
      <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="홍길동" />
      <Text style={styles.label}>휴대폰</Text>
      <TextInput
        style={styles.input}
        value={phone}
        onChangeText={setPhone}
        placeholder="010-0000-0000"
        keyboardType="phone-pad"
      />
      <Text style={styles.label}>배송지</Text>
      <TextInput
        style={[styles.input, { height: 90 }]}
        value={address}
        onChangeText={setAddress}
        placeholder="서울시 ..."
        multiline
      />
      <Text style={styles.label}>개인통관부호</Text>
      <TextInput
        style={styles.input}
        value={customsCode}
        onChangeText={(v) => setCustomsCode(normalizeCustomsCode(v).slice(0, 13))}
        placeholder="P123456789012"
        autoCapitalize="characters"
        maxLength={13}
      />

      <Text style={[styles.label, { marginTop: 8 }]}>결제 수단</Text>
      {methods.map((m) => (
        <Pressable
          key={m.id}
          onPress={() => setMethod(m.id)}
          style={[styles.method, method === m.id && styles.methodActive]}
        >
          <Text style={styles.methodText}>{m.label}</Text>
          <Text style={styles.hint}>연동 예정</Text>
        </Pressable>
      ))}

      <Pressable style={styles.btn} onPress={pay}>
        <Text style={styles.btnText}>결제하기 · {formatKrw(subtotal)}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { padding: 16, paddingBottom: 40 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  notice: {
    backgroundColor: "#f3f2ed",
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.12)",
  },
  noticeText: { fontSize: 13, lineHeight: 19, color: "rgba(11,18,16,0.72)" },
  hintBanner: {
    marginBottom: 12,
    fontSize: 13,
    color: "#1f4d3a",
    fontWeight: "600",
  },
  label: { marginTop: 10, marginBottom: 6, fontWeight: "600", fontSize: 13 },
  input: {
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.15)",
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    backgroundColor: "#fff",
  },
  method: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 14,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.12)",
    marginBottom: 8,
    backgroundColor: "#fff",
  },
  methodActive: { borderColor: "#1f4d3a", backgroundColor: "#f7f8f5" },
  methodText: { fontWeight: "600" },
  hint: { fontSize: 12, color: "rgba(11,18,16,0.45)" },
  btn: {
    marginTop: 20,
    backgroundColor: "#0b1210",
    paddingVertical: 16,
    alignItems: "center",
  },
  btnText: { color: "#f7f8f5", fontWeight: "700", letterSpacing: 0.3 },
});
