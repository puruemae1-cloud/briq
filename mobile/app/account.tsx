import { Link, router } from "expo-router";
import { useState } from "react";
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
import { STATUS_LABEL, useMobileOrders } from "../src/orders";
import { formatKrw } from "../src/data/products";
import { useCart } from "../src/cart";

export default function AccountScreen() {
  const { ready, currentUser, login, signup, logout, unlocked, lock, unlock } =
    useMobileAuth();
  const { count } = useCart();
  const { orders } = useMobileOrders(currentUser?.id);
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  if (!ready) {
    return (
      <View style={styles.center}>
        <Text>불러오는 중…</Text>
      </View>
    );
  }

  if (!currentUser) {
    return (
      <ScrollView contentContainerStyle={styles.page}>
        <Text style={styles.title}>{mode === "login" ? "로그인" : "회원가입"}</Text>
        <Text style={styles.lead}>
          가입 후 장바구니·주문·통관부호를 앱에서 확인할 수 있습니다.
        </Text>

        {mode === "signup" ? (
          <>
            <Text style={styles.label}>이름</Text>
            <TextInput style={styles.input} value={name} onChangeText={setName} />
          </>
        ) : null}

        <Text style={styles.label}>이메일</Text>
        <TextInput
          style={styles.input}
          autoCapitalize="none"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
        />
        <Text style={styles.label}>비밀번호</Text>
        <TextInput
          style={styles.input}
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        <Pressable
          style={styles.btn}
          onPress={async () => {
            const result =
              mode === "login"
                ? await login(email, password)
                : await signup({ email, password, name });
            if (!result.ok) Alert.alert("확인", result.message);
          }}
        >
          <Text style={styles.btnText}>
            {mode === "login" ? "로그인" : "가입하기"}
          </Text>
        </Pressable>

        <Pressable
          onPress={() => setMode(mode === "login" ? "signup" : "login")}
        >
          <Text style={styles.switch}>
            {mode === "login"
              ? "아직 회원이 아니신가요? 회원가입"
              : "이미 계정이 있으신가요? 로그인"}
          </Text>
        </Pressable>
      </ScrollView>
    );
  }

  if (!unlocked) {
    return (
      <View style={styles.center}>
        <Text style={styles.lockTitle}>Briq Locked</Text>
        <Text style={styles.lead}>앱을 잠금 해제해 주세요.</Text>
        <Pressable style={styles.btn} onPress={unlock}>
          <Text style={styles.btnText}>잠금 해제</Text>
        </Pressable>
        <Text style={styles.hint}>
          Face ID / 지문 연동은 expo-local-authentication 설치 후 연결됩니다.
        </Text>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <Text style={styles.brand}>My Briq</Text>
      <Text style={styles.title}>{currentUser.name} 님</Text>
      <Text style={styles.lead}>{currentUser.email}</Text>

      <View style={styles.cards}>
        <Link href="/cart" asChild>
          <Pressable style={styles.card}>
            <Text style={styles.cardLabel}>장바구니</Text>
            <Text style={styles.cardValue}>{count}개</Text>
          </Pressable>
        </Link>
        <Pressable style={styles.card}>
          <Text style={styles.cardLabel}>주문·결제</Text>
          <Text style={styles.cardValue}>{orders.length}건</Text>
        </Pressable>
        <Pressable
          style={styles.card}
          onPress={() => router.push("/checkout")}
        >
          <Text style={styles.cardLabel}>통관부호</Text>
          <Text style={styles.cardValue}>
            {currentUser.profile?.customsCode ? "저장됨" : "미등록"}
          </Text>
        </Pressable>
      </View>

      <Text style={styles.section}>최근 주문</Text>
      {orders.length === 0 ? (
        <Text style={styles.lead}>아직 주문이 없습니다.</Text>
      ) : (
        orders.slice(0, 5).map((o) => (
          <View key={o.id} style={styles.order}>
            <Text style={styles.orderId}>{o.id}</Text>
            <Text>
              {STATUS_LABEL[o.status]} · {formatKrw(o.totalKrw)}
            </Text>
            <Text style={styles.hint}>
              {o.trackingNumber
                ? `ACI EXPRESS ${o.trackingNumber}`
                : "송장 준비 중"}
            </Text>
          </View>
        ))
      )}

      <Pressable style={styles.ghost} onPress={lock}>
        <Text style={styles.ghostText}>앱 잠금 (생체인증 자리)</Text>
      </Pressable>
      <Pressable style={styles.ghost} onPress={logout}>
        <Text style={styles.ghostText}>로그아웃</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { padding: 16, paddingBottom: 40 },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    gap: 12,
  },
  brand: {
    fontSize: 12,
    letterSpacing: 3,
    textTransform: "uppercase",
    color: "#b7a16a",
    marginBottom: 4,
  },
  title: { fontSize: 28, fontWeight: "600", marginBottom: 6 },
  lockTitle: { fontSize: 28, fontWeight: "600" },
  lead: { color: "rgba(11,18,16,0.62)", lineHeight: 20, marginBottom: 12 },
  label: { marginTop: 10, marginBottom: 6, fontWeight: "600", fontSize: 13 },
  input: {
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.15)",
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: "#fff",
    fontSize: 15,
  },
  btn: {
    marginTop: 18,
    backgroundColor: "#0b1210",
    paddingVertical: 14,
    alignItems: "center",
  },
  btnText: { color: "#f7f8f5", fontWeight: "700" },
  switch: {
    marginTop: 16,
    textAlign: "center",
    color: "rgba(11,18,16,0.7)",
    fontWeight: "600",
  },
  cards: { gap: 10, marginVertical: 12 },
  card: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.12)",
    padding: 14,
  },
  cardLabel: {
    fontSize: 11,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: "#b7a16a",
    marginBottom: 4,
  },
  cardValue: { fontSize: 22, fontWeight: "600" },
  section: {
    marginTop: 18,
    marginBottom: 8,
    fontSize: 16,
    fontWeight: "700",
  },
  order: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.12)",
    padding: 12,
    marginBottom: 8,
    gap: 4,
  },
  orderId: { fontWeight: "700" },
  hint: { fontSize: 12, color: "rgba(11,18,16,0.5)" },
  ghost: {
    marginTop: 10,
    paddingVertical: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(11,18,16,0.15)",
  },
  ghostText: { fontWeight: "600", color: "rgba(11,18,16,0.7)" },
});
