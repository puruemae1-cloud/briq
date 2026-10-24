import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: "#0b1210" },
          headerTintColor: "#f7f8f5",
          headerTitleStyle: { fontWeight: "600", letterSpacing: 1 },
          contentStyle: { backgroundColor: "#f3f5f1" },
        }}
      >
        <Stack.Screen name="index" options={{ title: "Briq" }} />
        <Stack.Screen name="shop" options={{ title: "Shop" }} />
        <Stack.Screen name="product/[id]" options={{ title: "Product" }} />
        <Stack.Screen name="cart" options={{ title: "Cart" }} />
        <Stack.Screen name="checkout" options={{ title: "Checkout" }} />
        <Stack.Screen name="account" options={{ title: "My Briq" }} />
      </Stack>
    </>
  );
}
